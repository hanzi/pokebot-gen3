import sys
import typing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import jsonschema
from ruamel.yaml import YAML

from modules.Console import console
from modules.Roms import ROMS_DIRECTORY, ROM, ListAvailableRoms, LoadROMData

PROFILES_DIRECTORY = Path(__file__).parent.parent / "profiles"

metadata_schema = """
type: object
properties:
    version:
        type: integer
        enum:
            - 1
    rom:
        type: object
        properties:
            file_name:
                type: string
            game_code:
                type: string
            revision:
                type: integer
            language:
                type: string
                enum:
                    - E
                    - F
                    - D
                    - I
                    - J
                    - S
"""


@dataclass
class Profile:
    """
    Profiles are config directories that contain all data for a save game, such as saves,
    screenshots, stats, custom config, etc. -- except the ROM itself.

    The only requirements for a Profile are: There must be a subdirectory in `profiles/` with
    the name of the profile, and inside that directory there must be a file called
    `metadata.yml` that satisfies the `metadata_schema`.

    This metadata file specifies which game/ROM a save game is associated with, so we can
    load the correct ROM when selected.
    """

    rom: ROM
    path: Path
    last_played: typing.Union[datetime, None]


def ListAvailableProfiles() -> list[Profile]:
    if not PROFILES_DIRECTORY.is_dir():
        raise RuntimeError(f"Directory {str(PROFILES_DIRECTORY)} does not exist!")

    profiles = []
    for entry in PROFILES_DIRECTORY.iterdir():
        try:
            profiles.append(LoadProfile(entry))
        except RuntimeError:
            pass

    return profiles


def LoadProfileByName(name: str) -> Profile:
    return LoadProfile(PROFILES_DIRECTORY / name)


def LoadProfile(path) -> Profile:
    if not path.is_dir():
        raise RuntimeError("Path is not a valid profile directory.")

    metadata_file = path / "metadata.yml"
    if not metadata_file.is_file():
        raise RuntimeError("Path is not a valid profile directory.")

    try:
        metadata = YAML().load(metadata_file)
        jsonschema.validate(metadata, YAML().load(metadata_schema))
    except:
        console.print_exception(show_locals=True)
        console.print(f'[bold red]Metadata file for profile "{path.name}" is invalid![/]')
        sys.exit(1)

    current_state = path / "current_state.ss1"
    if current_state.exists():
        last_played = datetime.fromtimestamp(current_state.stat().st_mtime)
    else:
        last_played = None

    rom_file = ROMS_DIRECTORY / metadata["rom"]["file_name"]
    if rom_file.is_file():
        rom = LoadROMData(rom_file)
        return Profile(rom, path, last_played)
    else:
        for rom in ListAvailableRoms():
            if (
                rom.game_code == metadata["rom"]["game_code"]
                and rom.revision == metadata["rom"]["revision"]
                and rom.language == metadata["rom"]["language"]
            ):
                return Profile(rom, path, last_played)

    console.print(f'[bold red]Could not find a ROM for profile "{path.name}".[/]')
    sys.exit(1)


def ProfileDirectoryExists(name: str) -> bool:
    return (PROFILES_DIRECTORY / name).exists()


def CreateProfile(name: str, rom: ROM) -> Profile:
    profile_directory = PROFILES_DIRECTORY / name
    if profile_directory.exists():
        raise RuntimeError(f'There already is a profile called "{name}", cannot create a new one with that name.')

    profile_directory.mkdir()
    yaml = YAML()
    yaml.allow_unicode = False
    yaml.dump(
        {
            "version": 1,
            "rom": {
                "file_name": rom.file.name,
                "game_code": rom.game_code,
                "revision": rom.revision,
                "language": str(rom.language),
            },
        },
        profile_directory / "metadata.yml",
    )

    return Profile(rom, profile_directory, None)
