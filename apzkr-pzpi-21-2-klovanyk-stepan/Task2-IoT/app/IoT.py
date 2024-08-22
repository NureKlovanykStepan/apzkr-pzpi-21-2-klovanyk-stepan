import asyncio
import http.server
import json
import os
import sys
import threading
import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import IntEnum, Enum
from math import fabs
from pathlib import Path
from socket import gethostbyname, gethostname
from time import time

import requests

IOT_CODE_FILENAME = "IOT_REG"


class MessageCode(Enum):
    SUCCESS = (0, 255, 0)
    NO_FLASH_DRIVE = (255, 0, 0)
    NO_FILE = (0, 0, 255)
    READ_ERROR = (255, 0, 255)
    WRITE_ERROR = (0, 255, 255)
    CONNECTION_ERROR = (255, 255, 0)
    SERVER_BAD_RESPONSE = (255, 128, 64)
    NO_PORT_SPECIFIED = (37, 247, 229)


class StorageBase(ABC):

    def __init__(self, filename: str):
        self.filename = filename

    @dataclass
    class FetchedData:
        data: str
        result: 'MessageCode'

    @abstractmethod
    def read_no_check(self) -> str:
        raise NotImplemented

    @abstractmethod
    def write_no_check(self, data: str) -> None:
        raise NotImplemented

    @abstractmethod
    def is_file_present(self) -> bool:
        raise NotImplemented

    def get_file_path(self) -> Path:
        return Path(self.filename)

    def fetch(self):
        if not self.is_file_present():
            return StorageBase.FetchedData(data="", result=MessageCode.NO_FILE)

        try:
            return StorageBase.FetchedData(
                data=self.read_no_check(), result=MessageCode.SUCCESS
            )
        except Exception as e:
            print(e)
            return StorageBase.FetchedData(data="", result=MessageCode.READ_ERROR)

    def store(self, data: str):
        try:
            self.write_no_check(data)
            return MessageCode.SUCCESS
        except Exception as e:
            print(e)
            return MessageCode.WRITE_ERROR


class FlashStorageBase(StorageBase, ABC):
    @staticmethod
    @abstractmethod
    def is_flash_drive_present() -> bool:
        raise NotImplemented

    @staticmethod
    @abstractmethod
    def get_flash_drive_root() -> Path:
        raise NotImplemented

    def get_file_path(self) -> Path:
        return self.get_flash_drive_root() / self.filename

    def fetch(self):
        if not self.is_flash_drive_present():
            return StorageBase.FetchedData(data="", result=MessageCode.NO_FLASH_DRIVE)

        return super().fetch()

    def store(self, data: str):
        if not self.is_flash_drive_present():
            return MessageCode.NO_FLASH_DRIVE

        return super().store(data)


class ConfigStorageBase(StorageBase, ABC):
    def __init__(self):
        super().__init__("config.json")
        if not self.is_file_present():
            self.config = self.get_default_config()
            self.store_config()
            return
        try:
            self.config = self.fetch_config()
        except Exception as e:
            print(e)
            self.config = self.get_default_config()

    @dataclass
    class ConfigData:
        iot_registration_filename: str
        port: int
        latest_color_config: dict[str, any]
        registration_url: str

        def is_port_valid(self) -> bool:
            return 49152 <= self.port <= 65535

    @staticmethod
    def get_default_config() -> ConfigData:
        return ConfigStorageBase.ConfigData(
            iot_registration_filename="IOT_REG", port=-1, latest_color_config={},
            registration_url="http://localhost:8888/api/v2/light_devices/iot_registration_service/register/{}"
        )

    def fetch_config(self) -> ConfigData:
        return self.ConfigData(**json.loads(self.fetch().data))

    def store_config(self):
        self.store(json.dumps(asdict(self.config)))


class FlashDriveStateSimulator:
    class State(IntEnum):
        UNPLUGGED = False
        PLUGGED = True

    @staticmethod
    def _create_or_rename(state: State):
        if not (reverse_path := Path(FlashDriveStateSimulator.State(not state.value).name)).exists():
            Path(state.name).mkdir(exist_ok=True)
        else:
            reverse_path.rename(Path(state.name))

    @staticmethod
    def plug():
        FlashDriveStateSimulator._create_or_rename(FlashDriveStateSimulator.State.PLUGGED)

    @staticmethod
    def unplug():
        FlashDriveStateSimulator._create_or_rename(FlashDriveStateSimulator.State.UNPLUGGED)

    @staticmethod
    def is_plugged() -> bool:
        return Path(FlashDriveStateSimulator.State.PLUGGED.name).exists()

    @staticmethod
    def get_flash_drive_path():
        if not FlashDriveStateSimulator.is_plugged():
            return None
        return Path(FlashDriveStateSimulator.State.PLUGGED.name)


class StorageSimulator(StorageBase):
    def read_no_check(self) -> str:
        with open(self.get_file_path(), "r") as f:
            return f.read()

    def write_no_check(self, data: str) -> None:
        with open(self.get_file_path(), "w") as f:
            f.write(data)

    def get_file_path(self) -> Path:
        return Path(self.filename)

    def is_file_present(self) -> bool:
        return self.get_file_path().exists()


class ConfigStorageSimulator(StorageSimulator, ConfigStorageBase):
    pass


class FlashStorageSimulator(FlashStorageBase, StorageSimulator):
    @staticmethod
    def get_flash_drive_root() -> Path:
        return FlashDriveStateSimulator.get_flash_drive_path()

    @staticmethod
    def is_flash_drive_present() -> bool:
        return FlashDriveStateSimulator.is_plugged()


class TransitionalBase(ABC):
    @abstractmethod
    def get_distance(self) -> int:
        raise NotImplemented

    @abstractmethod
    def __add__(self, other: 'TransitionalBase'):
        raise NotImplemented

    @abstractmethod
    def __neg__(self):
        raise NotImplemented

    def __sub__(self, other: 'TransitionalBase'):
        return self + (-other)

    @abstractmethod
    def __mul__(self, other: int | float):
        raise NotImplemented

    def __floordiv__(self, other):
        return self * (1 / other)

    def __truediv__(self, other):
        return self * (1 / other)

    @abstractmethod
    def __iter__(self):
        raise NotImplemented


class RGB(TransitionalBase):
    def __add__(self, other: 'RGB'):
        return RGB(
            *[ch1 + ch2 for ch1, ch2 in zip(
                self, other
            )]
        )

    def __neg__(self):
        return RGB(-self.r, -self.g, -self.b)

    def __mul__(self, other: int | float):
        return RGB(*[round(ch * other) for ch in self])

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b

    def get_distance(self) -> int:
        return (self.r ** 2 + self.g ** 2 + self.b ** 2) ** 0.5

    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b


class Brightness(float, TransitionalBase):
    def __iter__(self):
        yield self

    def get_distance(self) -> float:
        return fabs(self)

    def __add__(self, other: 'Brightness'):
        return Brightness(super().__add__(other))

    def __sub__(self, other: 'Brightness'):
        return Brightness(super().__sub__(other))

    def __neg__(self):
        return Brightness(super().__neg__())

    def __mul__(self, other: int | float):
        return Brightness(super().__mul__(other))

    def __truediv__(self, other):
        return Brightness(super().__truediv__(other))


@dataclass
class TransitionalDataBase[T: TransitionalBase](ABC):
    value1: T
    value2: T | None

    def is_transitional(self) -> bool:
        return self.value2 is not None

    def get_closest_to(self, value: T) -> T:
        if not self.is_transitional():
            return self.value1

        if (self.value1 - value).get_distance() < (self.value2 - value).get_distance():
            return self.value1
        else:
            return self.value2

    def valueX(self, k: float) -> T:
        if not (0 <= k <= 1):
            raise ValueError("k must be between 0 and 1")

        if not self.is_transitional():
            return self.value1

        value_diff = self.value2 - self.value1
        return self.value1 + value_diff * k


class KValueBase(ABC):
    def __init__(self, duration_ms: int, tick_ms: int = 1, value=0):
        self.value = value
        if tick_ms <= 0:
            raise ValueError("tick_ms must be greater than 0")
        self.duration_ms = duration_ms
        self.tick_ms = tick_ms
        self.end_point_delay = duration_ms / 2
        self.direction_forward = True

    @property
    def k(self) -> float:
        return self.value / self.duration_ms

    @abstractmethod
    async def start_loop(self):
        raise NotImplemented


class StaticK(KValueBase):
    async def start_loop(self):
        self.value = 1


class OneWayK(KValueBase):
    async def start_loop(self):
        while True:
            t = time()
            await asyncio.sleep(self.tick_ms / 1000)
            fact_span = (time() - t) * 1000

            self.value += fact_span
            if self.value >= self.duration_ms:
                self.value = self.duration_ms
                break


class LoopedK(KValueBase):
    async def start_loop(self):
        while True:
            t = time()
            await asyncio.sleep(self.tick_ms / 1000)
            fact_span = (time() - t) * 1000

            self.value += fact_span * (1 if self.direction_forward else -1)
            if self.value >= self.duration_ms:
                self.value = self.duration_ms
                self.direction_forward = False
                await asyncio.sleep(self.end_point_delay / 1000)
            if self.value <= 0:
                self.value = 0
                self.direction_forward = True
                await asyncio.sleep(self.end_point_delay / 1000)


class LightControlBase(ABC):

    @staticmethod
    def rgb_to_int(rgb: RGB) -> int:
        return (rgb.r << 16) + (rgb.g << 8) + rgb.b

    @staticmethod
    def int_to_rgb(color: int) -> RGB:
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return RGB(r, g, b)

    @abstractmethod
    def set_color(self, color: int):
        raise NotImplemented

    @abstractmethod
    def set_two_colors(self, color1: int, color2: int, ms_delta: int):
        raise NotImplemented

    @abstractmethod
    def set_brightness(self, brightness: int):
        raise NotImplemented

    @abstractmethod
    def set_two_brightnesses(self, brightness1: int, brightness2: int, ms_delta: int):
        raise NotImplemented


class LightControl(LightControlBase):
    TICK_MS = 1

    async def set_color(self, color: RGB):
        await self.smooth_transition(color, 3000)
        self.transitional_color = TransitionalDataBase[RGB](color, None)
        self.current_color = color
        self._stop_colors_looping()
        self._stop_k_looping()

    def _stop_colors_looping(self):
        if self.looping_colors_task:
            self.looping_colors_task.cancel()
            self.looping_colors_task = None

    def _stop_k_looping(self):
        if self.k_looping_task:
            self.k_looping_task.cancel()
            self.k_looping_task = None

    async def smooth_transition(self, to: RGB, ms_delta: int):
        self._stop_colors_looping()
        self._stop_k_looping()

        self.transitional_color = TransitionalDataBase[RGB](self.current_color, to)
        self.k = OneWayK(ms_delta, self.TICK_MS)
        self.k_looping_task = asyncio.create_task(self.k.start_loop())
        self.looping_colors_task = asyncio.create_task(self.loop_colors())
        await self.k_looping_task

        self._stop_colors_looping()
        self._stop_k_looping()

    async def set_two_colors(self, color1: RGB, color2: RGB, ms_delta: int):
        await self.smooth_transition(color1, 3000)
        self.transitional_color = TransitionalDataBase[RGB](color1, color2)
        self.k = LoopedK(ms_delta, self.TICK_MS)
        self.k_looping_task = asyncio.create_task(self.k.start_loop())
        self.looping_colors_task = asyncio.create_task(self.loop_colors())
        await asyncio.gather(self.k_looping_task, self.looping_colors_task)

    async def loop_colors(self):
        while True:
            await asyncio.sleep(self.TICK_MS / 1000)
            self.current_color = self.transitional_color.valueX(self.k.k)

    def set_brightness(self, brightness: int):
        pass

    def set_two_brightnesses(self, brightness1: int, brightness2: int, ms_delta: int):
        pass

    @property
    def current_color(self) -> RGB:
        return self._current_color

    @current_color.setter
    def current_color(self, value: RGB):
        self._direct_color_change(value)
        self._current_color = value

    def _direct_color_change(self, value: RGB):
        self.canvas.itemconfig(self.rect, fill="#%02x%02x%02x" % (value.r, value.g, value.b))

    def __init__(self):
        self.canvas: tk.Canvas | None = None
        self.rect: int | None = None
        self._current_color = RGB(190, 190, 190)
        self.transitional_color = TransitionalDataBase[RGB](self.current_color, None)
        self.k: KValueBase = StaticK(1)

        self.looping_colors_task: asyncio.Task | None = None
        self.k_looping_task: asyncio.Task | None = None

        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=512, height=512)
        self.canvas.pack()

        self.rect = self.canvas.create_rectangle(0, 0, 512, 512, fill="#999999")


@dataclass
class RegisterResponse:
    code: str
    port: int


class DeviceConfig:
    """
    Configuration used for the device.

    :var color: :class:`int` - Color
    :var color_alter: :class:`int` - Color alter
    :var color_alter_ms_delta: :class:`int` - Color alter ms delta
    """

    def __init__(
            self, color: int, color_alter: int = None, color_alter_ms_delta: int = None
    ):
        print(color, color_alter, color_alter_ms_delta)
        self.color = color
        self.color_alter = color_alter
        self.color_alter_ms_delta = color_alter_ms_delta

    def to_dict(self):
        return self.__dict__

    def serialize(self):
        return json.dumps(self.to_dict())

    @classmethod
    def deserialize(cls, data):
        return cls.from_dict(json.loads(data))

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


async def flash_drive_present_case(
        config_storage: ConfigStorageBase, flash_storage: FlashStorageBase, control: LightControl
):
    data = flash_storage.fetch()
    control.current_color = RGB(*data.result.value)
    if data.data:
        host = gethostbyname(gethostname())
        url = config_storage.config.registration_url.format(f"{data.data}/{host}")
        try:
            response = requests.post(url)
            if response.status_code == 200:
                _ = asyncio.create_task(control.set_two_colors(RGB(0, 255, 0), RGB(255, 255, 255), 250))
                await asyncio.sleep(5)
                task = asyncio.create_task(control.set_color(RGB(0, 0, 0)))
                reg_response = RegisterResponse(**response.json())
                flash_storage.store(reg_response.code)
                config_storage.config.port = reg_response.port
                config_storage.store_config()
                await task
            else:
                print(response_text := response.text)

                try:
                    with open(flash_storage.get_flash_drive_root() / "latest_error.log", "w+") as file:
                        file.write(response_text)
                except Exception:
                    pass

                control.current_color = RGB(*MessageCode.SERVER_BAD_RESPONSE.value)
        except requests.ConnectionError:
            control.current_color = RGB(*MessageCode.CONNECTION_ERROR.value)


class LightingConfigAdapter:
    def __init__(self, control: LightControl, config: DeviceConfig):
        self.config = config
        self.control = control

    async def color_change(self):
        if not self.config or not self.config.color:
            await self.control.set_color(RGB(0, 0, 0))
        if not self.config.color_alter or not self.config.color_alter_ms_delta:
            await self.control.set_color(self.control.int_to_rgb(self.config.color))
        else:
            await self.control.set_two_colors(
                color1=self.control.int_to_rgb(self.config.color),
                color2=self.control.int_to_rgb(self.config.color_alter),
                ms_delta=self.config.color_alter_ms_delta
            )


class HandleNewConfig(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, control: LightControl, on_config_change, **kwargs):
        self.control = control
        self.on_config_change = on_config_change
        super().__init__(*args, **kwargs)

    def _change_color(self, config_data: DeviceConfig):
        def threaded_color_change():
            asyncio.run(LightingConfigAdapter(self.control, config_data).color_change())

        threading.Thread(target=threaded_color_change).start()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            json_data = json.loads(post_data)
            config_data = DeviceConfig(**json_data)

            self._change_color(config_data)

            # if config_data.color_alter is None:
            #     async def set_color():
            #         await asyncio.create_task(
            #             self.control.set_color(self.control.int_to_rgb(config_data.color))
            #         )
            #
            #     def init_set_color():
            #         asyncio.run(set_color())
            #
            #     threading.Thread(target=init_set_color).start()
            #
            # else:
            #     async def set_multiple_colors():
            #         await asyncio.create_task(
            #             self.control.set_two_colors(
            #                 self.control.int_to_rgb(config_data.color),
            #                 self.control.int_to_rgb(config_data.color_alter),
            #                 config_data.color_alter_ms_delta
            #             )
            #         )
            #
            #     def init_set_multiple_colors():
            #         asyncio.run(set_multiple_colors())
            #
            #     threading.Thread(target=init_set_multiple_colors).start()

            response_data = "config transferred!"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

            self.on_config_change(config_data.to_dict())

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON data")


async def general_case(config_storage: ConfigStorageBase, control: LightControl):
    port = config_storage.config.port
    if port == -1:
        control.current_color = MessageCode.NO_PORT_SPECIFIED.value
    else:
        async def emit_success():
            _ = asyncio.create_task(control.set_two_colors(RGB(0, 255, 0), RGB(0, 0, 0), 125))
            await asyncio.sleep(5)
            await LightingConfigAdapter(
                control,
                DeviceConfig(
                    **config_storage.config.latest_color_config
                ) if config_storage.config.latest_color_config
                else DeviceConfig(0)
            ).color_change()

        def on_config_change(new_config: dict):
            config_storage.config.latest_color_config = new_config
            config_storage.store_config()

        task = asyncio.create_task(emit_success())
        server_address = ("", port)
        httpd = http.server.HTTPServer(
            server_address, lambda *args, **kwargs: HandleNewConfig(
                *args,
                control=control,
                on_config_change=on_config_change,
                **kwargs
            )
        )

        def init_server():
            httpd.serve_forever()

        threading.Thread(target=init_server).start()
        await asyncio.gather(task)


def REBOOT():
    os.execv(sys.executable, ['python'] + sys.argv)


async def main(config_storage: ConfigStorageBase, flash_storage: FlashStorageBase):
    control: LightControl | None = None
    control_event = threading.Event()

    def init_tk():
        nonlocal control
        control = LightControl()
        control_event.set()
        control.root.mainloop()

    threading.Thread(target=init_tk).start()

    control_event.wait()
    if flash_storage.is_flash_drive_present():
        await flash_drive_present_case(config_storage, flash_storage, control)
        await asyncio.sleep(3)
        REBOOT()
    else:
        await general_case(config_storage, control)


if __name__ == "__main__":
    FlashDriveStateSimulator.unplug()
    asyncio.run(
        main(
            cfg_storage := ConfigStorageSimulator(),
            FlashStorageSimulator(cfg_storage.fetch_config().iot_registration_filename)
        )
    )
