import os
import re
import shutil
from dataclasses import dataclass

import keyvalues3 as kv3
from iterfzf import iterfzf
from rich.text import Text
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import DataTable, Footer, Header

from config import Config


@dataclass
class Hero:
    id: int
    name: str
    disabled: bool
    hero_labs: bool
    ability_weapon: str
    ability_1: str
    ability_2: str
    ability_3: str
    ability_4: str


def colorize_bool(value: bool) -> Text:
    if value:
        return Text("True", style="green")
    else:
        return Text("False", style="red")


class AbilityApp(App):
    BINDINGS = [
        ("f", "find_hero", "Find Hero"),
        ("l", "toggle_localization", "Toggle Localization"),
        ("ctrl+s", "save", "Save"),
    ]
    TITLE = "Artemon121's Hero Abilities Swapper"

    heroes: dict[str, Hero]
    heroes_vdata: kv3.KV3File
    abilities_vdata: kv3.KV3File
    ability_users: dict[str, list[str]] = {}
    localized_heroes: dict[str, str] = {}
    localized_abilities: dict[str, str] = {}
    localize_table = False
    aditional_abilities_localization: dict[str, str] = {}
    config: Config

    def load_heroes(self) -> None:
        """Load heroes from heroes.vdata"""
        self.heroes_vdata = kv3.read(str(self.config.heroes_vdata_path))
        heroes = {}
        for key, value in self.heroes_vdata.items():
            if key == "generic_data_type":
                continue

            try:
                hero = Hero(
                    id=value["m_HeroID"],
                    name=key,
                    disabled=value["m_bDisabled"],
                    hero_labs=value["m_bInDevelopment"],
                    ability_weapon=value["m_mapBoundAbilities"]["ESlot_Weapon_Primary"],
                    ability_1=value["m_mapBoundAbilities"]["ESlot_Signature_1"],
                    ability_2=value["m_mapBoundAbilities"]["ESlot_Signature_2"],
                    ability_3=value["m_mapBoundAbilities"]["ESlot_Signature_3"],
                    ability_4=value["m_mapBoundAbilities"]["ESlot_Signature_4"],
                )
            except KeyError:
                continue

            heroes[key] = hero

        self.heroes = heroes

    def load_abilities(self) -> None:
        """Load abilities from abilities.vdata"""
        self.abilities_vdata = kv3.read(self.config.abilities_vdata_path)
        self.abilities_vdata.pop("_include")

    def load_locale(self) -> None:
        """Load localization for heroes and abilities."""
        citadel_gc_path = (
            self.config.deadlock_path
            / "game"
            / "citadel"
            / "resource"
            / "localization"
            / "citadel_gc"
            / "citadel_gc_english.txt"
        )
        citadel_heroes_path = (
            self.config.deadlock_path
            / "game"
            / "citadel"
            / "resource"
            / "localization"
            / "citadel_heroes"
            / "citadel_heroes_english.txt"
        )

        pattern = r'"([^"]*)"\s+(?:"(.*)")'
        locale_citadel_gc = {}
        locale_citadel_heroes = {}

        with open(citadel_gc_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            for line in lines:
                match = re.search(pattern, line)
                if not match:
                    continue
                locale_citadel_gc[match.group(1)] = match.group(2)

        with open(citadel_heroes_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            for line in lines:
                match = re.search(pattern, line)
                if not match:
                    continue
                locale_citadel_heroes[match.group(1)] = match.group(2)

        for name, hero in self.heroes.items():
            localized_name = locale_citadel_gc.get(name, name)
            self.localized_heroes[name] = localized_name

            abilities = {
                "Weapon": hero.ability_weapon,
                "1": hero.ability_1,
                "2": hero.ability_2,
                "3": hero.ability_3,
                "Ult": hero.ability_4,
            }

            for slot, ability in abilities.items():
                if ability not in self.ability_users:
                    self.ability_users[ability] = []

                self.ability_users[ability].append(f"{localized_name} {slot}")

        for name, hero in self.heroes.items():
            localized_name = self.localized_heroes[name]
            self.localized_abilities[hero.ability_weapon] = f"{localized_name} Weapon"

            for ability in [
                hero.ability_1,
                hero.ability_2,
                hero.ability_3,
                hero.ability_4,
            ]:
                if ability in self.localized_abilities:
                    continue

                base_name = locale_citadel_heroes.get(ability, ability)
                users = self.ability_users.get(ability, [])
                self.localized_abilities[ability] = f"{base_name} ({', '.join(users)})"

        for name in self.abilities_vdata.keys():
            if (
                name == "generic_data_type"
                or name in self.localized_abilities
                or "upgrade" in name
                or locale_citadel_heroes.get(name, "") == "Melee"
            ):
                continue
            ability_localized = locale_citadel_heroes.get(name, name)
            self.localized_abilities[name] = f"{ability_localized} (Unknown)"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield DataTable()

    def on_mount(self) -> None:
        self.config = Config.load()
        self.theme = self.config.theme
        self.load_heroes()
        self.load_abilities()
        self.load_locale()
        self.populate_table()

    def populate_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(True)

        for key, label in [
            ("id", "ID"),
            ("name", "Name"),
            ("disabled", "Disabled?"),
            ("hero_labs", "Hero Labs?"),
            ("ability_weapon", "Weapon"),
            ("ability_1", "Ability 1"),
            ("ability_2", "Ability 2"),
            ("ability_3", "Ability 3"),
            ("ability_4", "Ability 4"),
        ]:
            table.add_column(label, key=key)

        for name, hero in self.heroes.items():
            if not self.localize_table:
                table.add_row(
                    hero.id,
                    name,
                    colorize_bool(hero.disabled),
                    colorize_bool(hero.hero_labs),
                    hero.ability_weapon,
                    hero.ability_1,
                    hero.ability_2,
                    hero.ability_3,
                    hero.ability_4,
                    key=hero.name,
                )
            else:
                table.add_row(
                    hero.id,
                    self.localized_heroes[name],
                    colorize_bool(hero.disabled),
                    colorize_bool(hero.hero_labs),
                    self.localized_abilities[hero.ability_weapon],
                    self.localized_abilities[hero.ability_1],
                    self.localized_abilities[hero.ability_2],
                    self.localized_abilities[hero.ability_3],
                    self.localized_abilities[hero.ability_4],
                    key=hero.name,
                )

    def action_toggle_localization(self) -> None:
        self.localize_table = not self.localize_table
        table = self.query_one(DataTable)
        cursor_pos = table.cursor_coordinate
        self.populate_table()
        table.move_cursor(row=cursor_pos.row, column=cursor_pos.column)

    def ensure_signature(self, ability_name: str) -> str:
        """
        Creates a copy of the ability with the ability type set to Signature and returns it's name.

        If the ability type is already Signature, returns the input name.
        """
        if (
            self.abilities_vdata[ability_name]["m_eAbilityType"]
            == "EAbilityType_Signature"
        ):
            return ability_name

        generated_name = f"{ability_name}_signature"
        self.abilities_vdata[generated_name] = {
            "_multibase": [ability_name],
            "m_eAbilityType": "EAbilityType_Signature",
        }
        self.aditional_abilities_localization[generated_name] = ability_name
        return generated_name

    def ensure_ultimate(self, ability_name: str) -> str:
        """
        Creates a copy of the ability with the ability type set to Ultimate and returns it's name.

        If the ability type is already Ultimate, returns the input name.
        """
        if (
            self.abilities_vdata[ability_name]["m_eAbilityType"]
            == "EAbilityType_Ultimate"
        ):
            return ability_name

        generated_name = f"{ability_name}_ultimate"
        self.abilities_vdata[generated_name] = {
            "_multibase": [ability_name],
            "m_eAbilityType": "EAbilityType_Ultimate",
        }
        self.aditional_abilities_localization[generated_name] = ability_name
        return generated_name

    def ensure_unique(self, abilities: list[str]) -> list[str]:
        """Given a list of ability names, generate new ones if the ability is not unique"""
        count_map = {}
        output = []
        for ability_name in abilities:
            if ability_name not in count_map.keys():
                count_map[ability_name] = 0
                output.append(ability_name)
                continue
            count_map[ability_name] += 1

            generated_name = f"{ability_name}_{count_map[ability_name]}"
            self.abilities_vdata[generated_name] = {
                "_multibase": [ability_name],
            }
            self.aditional_abilities_localization[generated_name] = ability_name
            output.append(generated_name)

        return output

    def save_aditional_localization(self) -> None:
        for language in [
            "brazilian",
            "czech",
            "english",
            "french",
            "german",
            "indonesian",
            "italian",
            "japanese",
            "koreana",
            "latam",
            "polish",
            "russian",
            "schinese",
            "spanish",
            "thai",
            "turkish",
            "ukrainian",
        ]:
            citadel_heroes_path = (
                self.config.deadlock_path
                / "game"
                / "citadel"
                / "resource"
                / "localization"
                / "citadel_heroes"
                / f"citadel_heroes_{language}.txt"
            )
            out_heroes_path = (
                self.config.output_path
                / "resource"
                / "localization"
                / "citadel_heroes"
                / f"citadel_heroes_{language}.txt"
            )
            os.makedirs(out_heroes_path.parent, exist_ok=True)
            shutil.copy(citadel_heroes_path, out_heroes_path)

            with open(out_heroes_path, "r", encoding="utf-8") as file:
                content = file.read()
                lines = []
                for key, value in self.aditional_abilities_localization.items():
                    match = re.search(rf'"{value}"\s+(?:"(.*)")', content)
                    if match is None:
                        continue
                    lines.append(f'"{key}" "{match.group(1)}"')

            with open(out_heroes_path, "w", encoding="utf-8") as file:
                file.write(
                    re.sub(
                        r'"Tokens"\s*\n\s*{',
                        f'"Tokens" {{\n\t\t{"\n\t\t".join(lines)}',
                        content,
                    )
                )

    def action_save(self) -> None:
        """Save the modified heroes.vdata to the output path."""
        for key, value in self.heroes_vdata.items():
            if key == "generic_data_type":
                continue

            hero = self.heroes.get(key)
            if hero is None:
                continue

            value["m_bDisabled"] = hero.disabled
            value["m_bPlayerSelectable"] = True
            value["m_bInDevelopment"] = hero.hero_labs
            value["m_bAvailableInHeroLabs"] = hero.hero_labs
            value["m_mapBoundAbilities"]["ESlot_Weapon_Primary"] = hero.ability_weapon

            abilities = self.ensure_unique(
                [
                    self.ensure_signature(hero.ability_1),
                    self.ensure_signature(hero.ability_2),
                    self.ensure_signature(hero.ability_3),
                    self.ensure_ultimate(hero.ability_4),
                ]
            )

            for i, ability in enumerate(abilities):
                value["m_mapBoundAbilities"][f"ESlot_Signature_{i + 1}"] = ability

        os.makedirs(self.config.output_path, exist_ok=True)
        kv3.write(self.heroes_vdata, str(self.config.output_path / "heroes.vdata"))
        kv3.write(
            self.abilities_vdata, str(self.config.output_path / "abilities.vdata")
        )
        self.save_aditional_localization()
        self.notify(f"Saved to {str(self.config.output_path)}")

    def action_find_hero(self) -> None:
        """Find hero by localized name and select it in the table"""
        table = self.query_one(DataTable)
        with self.suspend():
            try:
                selected_item: str = iterfzf(
                    self.localized_heroes.values(),
                    case_sensitive=False,
                )
            except KeyboardInterrupt:
                return

        reversed_localized_heroes = {
            value: key for key, value in self.localized_heroes.items()
        }
        selected_hero = reversed_localized_heroes[selected_item]
        row = table.get_row_index(selected_hero)
        column = table.get_column_index("name")
        table.move_cursor(row=row, column=column, animate=True)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        table = event.data_table
        cell_key = table.coordinate_to_cell_key(event.coordinate)
        column_key = cell_key.column_key.value
        hero_name = cell_key.row_key.value
        if column_key is None or hero_name is None:
            return
        if column_key.startswith("ability_"):
            return self.swap_ability(event.coordinate)
        if column_key == "disabled" or column_key == "hero_labs":
            new_value: bool = not self.heroes[hero_name].__getattribute__(column_key)
            self.heroes[hero_name].__setattr__(column_key, new_value)
            table.update_cell_at(event.coordinate, colorize_bool(new_value))

    def swap_ability(self, cell_coordinate: Coordinate) -> None:
        """Swap ability in the given table cell"""
        table = self.query_one(DataTable)
        cell_key = table.coordinate_to_cell_key(cell_coordinate)
        column_key = cell_key.column_key.value
        hero_name = cell_key.row_key.value
        if column_key is None or hero_name is None:
            return

        with self.suspend():
            try:
                selected_item: str = iterfzf(
                    self.localized_abilities.values(),
                    case_sensitive=False,
                )
            except KeyboardInterrupt:
                return

        reversed_localized_abilities = {
            value: key for key, value in self.localized_abilities.items()
        }
        selected_ability = reversed_localized_abilities[selected_item]

        self.heroes[hero_name].__setattr__(column_key, selected_ability)
        if not self.localize_table:
            table.update_cell_at(cell_coordinate, selected_ability)
        else:
            table.update_cell_at(
                cell_coordinate, self.localized_abilities[selected_ability]
            )


if __name__ == "__main__":
    app = AbilityApp()
    app.run()
