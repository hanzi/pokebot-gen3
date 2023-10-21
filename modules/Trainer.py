from enum import IntEnum, Enum

from modules.Game import DecodeString
from modules.Gui import GetROM
from modules.Memory import GetSaveBlock, ReadSymbol, unpack_uint16
from modules.data.MapData import MapRSE, MapFRLG


# https://github.com/pret/pokeemerald/blob/104e81b359d287668cee613f6604020a6e7228a3/include/global.fieldmap.h
class AvatarFlags(IntEnum):
    PLAYER_AVATAR_FLAG_ON_FOOT = 1 << 0
    PLAYER_AVATAR_FLAG_MACH_BIKE = 1 << 1
    PLAYER_AVATAR_FLAG_ACRO_BIKE = 1 << 2
    PLAYER_AVATAR_FLAG_SURFING = 1 << 3
    PLAYER_AVATAR_FLAG_UNDERWATER = 1 << 4
    PLAYER_AVATAR_FLAG_CONTROLLABLE = 1 << 5
    PLAYER_AVATAR_FLAG_FORCED_MOVE = 1 << 6
    PLAYER_AVATAR_FLAG_DASH = 1 << 7


class RunningStates(IntEnum):
    NOT_MOVING = 0
    TURN_DIRECTION = 1
    MOVING = 2


class TileTransitionStates(IntEnum):
    NOT_MOVING = 0
    TRANSITIONING = 1  # transition between tiles
    CENTERING = 2  # on the frame in which you have centered on a tile but are about to keep moving,
    # even if changing directions. Used for a ledge hop, since you are transitioning


class AcroBikeStates(IntEnum):
    NORMAL = 0
    TURNING = 1
    STANDING_WHEELIE = 2
    HOPPING_WHEELIE = 3
    MOVING_WHEELIE = 4


class FacingDirection(Enum):
    Down = 0x11
    Up = 0x22
    Left = 0x33
    Right = 0x44


class Trainer:
    def __init__(self):
        if GetROM().game_title in ["POKEMON EMER", "POKEMON RUBY", "POKEMON SAPP"]:
            self.map_data = MapRSE
            self.map_offset = 0
        else:
            self.map_data = MapFRLG
            self.map_offset = 1

    def GetName(self) -> str:
        return DecodeString(GetSaveBlock(2, size=8))

    def GetGender(self) -> str:
        return "girl" if int.from_bytes(GetSaveBlock(2, 0x8, 1), byteorder="little") else "boy"

    def GetTID(self) -> int:
        return unpack_uint16(GetSaveBlock(2, 0xA, 2))

    def GetSID(self) -> int:
        return unpack_uint16(GetSaveBlock(2, 0xC, 2))

    def GetMap(self) -> tuple:
        b_gTasks = ReadSymbol("gTasks", 0x58, 4)
        return (int(b_gTasks[self.map_offset + 1]), int(b_gTasks[self.map_offset]))

    def GetMapName(self) -> str:
        try:
            return self.map_data(self.GetMap()).name
        except ValueError:
            return "UNKNOWN"

    def GetCoords(self) -> tuple:
        b_gObjectEvents = ReadSymbol("gObjectEvents", 16, 3)
        return (int(b_gObjectEvents[0]) - 7, int(b_gObjectEvents[2]) - 7)

    def GetOnBike(self) -> bool:
        b_gPlayerAvatar = ReadSymbol("gPlayerAvatar", size=1)
        return (
            int(b_gPlayerAvatar[0])
            & (AvatarFlags.PLAYER_AVATAR_FLAG_MACH_BIKE | AvatarFlags.PLAYER_AVATAR_FLAG_ACRO_BIKE)
        ) != 0

    def GetRunningState(self) -> int:
        b_gPlayerAvatar = ReadSymbol("gPlayerAvatar", offset=2, size=1)
        return int(b_gPlayerAvatar[0])

    def GetTileTransitionState(self) -> int:
        b_gPlayerAvatar = ReadSymbol("gPlayerAvatar", offset=3, size=1)
        return int(b_gPlayerAvatar[0])

    def GetAcroBikeState(self) -> int:
        b_gPlayerAvatar = ReadSymbol("gPlayerAvatar", offset=8, size=1)
        return int(b_gPlayerAvatar[0])

    def GetFacingDirection(self) -> str:
        b_gObjectEvents = ReadSymbol("gObjectEvents", 24, 1)
        return FacingDirection(int(b_gObjectEvents[0])).name


trainer = Trainer()
