"""
Hardware System Architect Agent - Multi-Subsystem Hardware Foundry.
Devashri S Embedded System Technologies - MAH Quantum.
Powered by KiCad Core EDA.
"""

from typing import Dict, Any, List
from .base_agent import BaseHardwareAgent


class ArchitectAgent(BaseHardwareAgent):
    def __init__(self):
        super().__init__(
            name="SystemArchitect",
            role_description="Principal Embedded Hardware Architect and BOM Specialist"
        )
        self.set_system_prompt(
            "You are a Principal Embedded Systems Hardware Architect at MAH Quantum. "
            "Synthesize industrial-grade hardware architectures from natural language specs. "
            "Return structured JSON with components, power trees, pinout mappings, and design rules."
        )

    def analyze_requirements(self, user_prompt: str) -> Dict[str, Any]:
        return self.call_llm(user_prompt)

    def synthesize_heuristic(self, prompt: str) -> Dict[str, Any]:
        """
        Industrial-grade deterministic embedded systems architecture engine.
        Supports 5 major embedded categories:
          1. Raspberry Pi RP2040 Compute System
          2. STM32 Motion / Robotics Driver
          3. Environmental Multi-Sensor IoT Node
          4. Automotive Dual CAN-FD / LIN Gateway
          5. Precision Audio / DSP Processor
        """
        lower = prompt.lower()

        # ── Archetype 1: Raspberry Pi RP2040 Compute System ────────────────────
        if "rp2040" in lower or "raspberry pi" in lower:
            if "audio" in lower or "dac" in lower or "sound" in lower:
                return self._build_rp2040_audio_architecture()
            return self._build_rp2040_compute_architecture()

        # ── Archetype 2: STM32 Motion / Robotics Controller ───────────────────
        elif "stm32" in lower or "motion" in lower or "stepper" in lower or "motor" in lower:
            return self._build_stm32_motion_architecture()

        # ── Archetype 3: Automotive Dual CAN-FD / LIN Gateway ─────────────────
        elif "automotive" in lower or "gateway" in lower or ("can" in lower and "lin" in lower):
            return self._build_automotive_gateway_architecture()

        # ── Archetype 4: Environmental Multi-Sensor IoT Node ──────────────────
        elif "sensor" in lower or "bme280" in lower or "lipo" in lower or "solar" in lower:
            return self._build_sensor_iot_architecture()

        # ── Archetype 5 (Default): High-Performance IoT Gateway (ESP32-S3) ────
        else:
            return self._build_esp32_iot_architecture()

    def _build_rp2040_compute_architecture(self) -> Dict[str, Any]:
        mcu = {
            "reference": "U1",
            "mpn": "RP2040",
            "lib_id": "MCU_RaspberryPi:RP2040",
            "footprint": "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
            "package": "QFN-56",
            "supply_voltage": "3.3V / 1.1V Core"
        }
        flash = {
            "reference": "U2",
            "mpn": "W25Q128JVS",
            "lib_id": "Memory_Flash:W25Q128JVS",
            "footprint": "Package_SO:SOIC-8_5.23x5.23mm_P1.27mm",
            "package": "SOIC-8",
            "role": "16MB High-Speed QSPI Flash Memory"
        }
        ldo = {
            "reference": "U3",
            "mpn": "NCP115AMX330TCG",
            "lib_id": "Regulator_Linear:NCP115AMX330",
            "footprint": "Package_TO_SOT_SMD:SOT-23-5",
            "package": "SOT-23-5",
            "role": "High-PSRR 300mA 3.3V Low-Dropout Regulator"
        }
        usb = {
            "reference": "J1",
            "mpn": "TYPE-C-31-M-12",
            "lib_id": "Connector:USB_C_Receptacle_USB2.0_16P",
            "footprint": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
            "role": "USB-C 2.0 Interface for UF2 Flashing and Debugging"
        }
        xtal = {
            "reference": "Y1",
            "mpn": "ABLS-12.000MHZ-B4-T",
            "lib_id": "Device:Crystal",
            "footprint": "Crystal:Crystal_SMD_HC49-SD",
            "role": "12.000 MHz Master Oscillator Crystal"
        }
        components = [mcu, flash, ldo, usb, xtal]
        nets = [
            {"net": "GND", "type": "power"},
            {"net": "+3V3", "type": "power"},
            {"net": "VBUS", "type": "power"},
            {"net": "+1V1_CORE", "type": "power"},
            {"net": "USB_DP", "type": "diff_pair"},
            {"net": "USB_DN", "type": "diff_pair"},
            {"net": "QSPI_CLK", "type": "high_speed"},
            {"net": "QSPI_CS", "type": "control"},
            {"net": "QSPI_IO0", "type": "data"},
            {"net": "QSPI_IO1", "type": "data"},
            {"net": "QSPI_IO2", "type": "data"},
            {"net": "QSPI_IO3", "type": "data"},
        ]
        return {
            "project_name": "RP2040_Embedded_Compute_System",
            "archetype": "rp2040_compute",
            "mcu": mcu,
            "components": components,
            "nets": nets,
            "board_dims": (65.0, 35.0),
            "rules": {"trace_width_power_mm": 0.5, "trace_width_signal_mm": 0.2}
        }

    def _build_stm32_motion_architecture(self) -> Dict[str, Any]:
        mcu = {
            "reference": "U1",
            "mpn": "STM32F405RGT6",
            "lib_id": "MCU_ST_STM32F4:STM32F405RGTx",
            "footprint": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
            "package": "LQFP-64",
            "supply_voltage": "3.3V"
        }
        driver1 = {
            "reference": "U2",
            "mpn": "TMC2209-LA",
            "lib_id": "Driver_Motor:TMC2209",
            "footprint": "Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.25x3.25mm",
            "role": "Ultra-Silent 2A Stepper Motor Driver with StealthChop"
        }
        buck = {
            "reference": "U3",
            "mpn": "TPS54302DDCR",
            "lib_id": "Regulator_Switching:TPS54302DDC",
            "footprint": "Package_TO_SOT_SMD:SOT-23-6",
            "role": "24V to 3.3V 3A Step-Down Buck Converter"
        }
        rs485 = {
            "reference": "U4",
            "mpn": "MAX485ESA+",
            "lib_id": "Interface_UART:MAX485E",
            "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "role": "Isolated High-Speed RS485 Industrial Bus Transceiver"
        }
        return {
            "project_name": "STM32_Industrial_Motion_Controller",
            "archetype": "stm32_motion",
            "mcu": mcu,
            "components": [mcu, driver1, buck, rs485],
            "nets": [
                {"net": "GND", "type": "power"},
                {"net": "+3V3", "type": "power"},
                {"net": "+24V", "type": "power"},
                {"net": "STEP_X", "type": "signal"},
                {"net": "DIR_X", "type": "signal"},
                {"net": "RS485_A", "type": "diff_pair"},
                {"net": "RS485_B", "type": "diff_pair"},
            ],
            "board_dims": (80.0, 50.0),
            "rules": {"trace_width_power_mm": 0.8, "trace_width_signal_mm": 0.25}
        }

    def _build_automotive_gateway_architecture(self) -> Dict[str, Any]:
        mcu = {
            "reference": "U1",
            "mpn": "ESP32-S3-WROOM-1-N16R8",
            "lib_id": "RF_Module:ESP32-S3-WROOM-1",
            "footprint": "RF_Module:ESP32-S3-WROOM-1",
            "supply_voltage": "3.3V"
        }
        can1 = {
            "reference": "U2",
            "mpn": "SN65HVD230DR",
            "lib_id": "Interface_CAN_LIN:SN65HVD230",
            "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "role": "Primary High-Speed CAN-FD Physical Transceiver"
        }
        can2 = {
            "reference": "U3",
            "mpn": "SN65HVD230DR",
            "lib_id": "Interface_CAN_LIN:SN65HVD230",
            "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "role": "Secondary Isolated CAN-FD Bus Transceiver"
        }
        buck = {
            "reference": "U4",
            "mpn": "TPS54302DDCR",
            "lib_id": "Regulator_Switching:TPS54302DDC",
            "footprint": "Package_TO_SOT_SMD:SOT-23-6",
            "role": "Automotive 9-36V Load-Dump Safe Buck Regulator"
        }
        return {
            "project_name": "Automotive_Dual_CAN_Gateway",
            "archetype": "automotive_gateway",
            "mcu": mcu,
            "components": [mcu, can1, can2, buck],
            "nets": [
                {"net": "GND", "type": "power"},
                {"net": "+3V3", "type": "power"},
                {"net": "+12V_BAT", "type": "power"},
                {"net": "CAN1_H", "type": "diff_pair"},
                {"net": "CAN1_L", "type": "diff_pair"},
                {"net": "CAN2_H", "type": "diff_pair"},
                {"net": "CAN2_L", "type": "diff_pair"},
            ],
            "board_dims": (75.0, 48.0),
            "rules": {"trace_width_power_mm": 0.6, "trace_width_signal_mm": 0.2}
        }

    def _build_sensor_iot_architecture(self) -> Dict[str, Any]:
        mcu = {
            "reference": "U1",
            "mpn": "ESP32-C3-MINI-1",
            "lib_id": "RF_Module:ESP32-C3-MINI-1",
            "footprint": "RF_Module:ESP32-C3-MINI-1",
            "supply_voltage": "3.3V"
        }
        sensor_env = {
            "reference": "U2",
            "mpn": "BME280",
            "lib_id": "Sensor_Pressure:BME280",
            "footprint": "Package_LGA:LGA-8_2.5x2.5mm_P0.65mm_Clockwise",
            "role": "Precision Barometric Pressure, Humidity & Temperature Sensor"
        }
        sensor_imu = {
            "reference": "U3",
            "mpn": "MPU-6050",
            "lib_id": "Sensor_Motion:MPU-6050",
            "footprint": "Package_DFN_QFN:QFN-24_4x4mm_P0.5mm",
            "role": "6-Axis MotionTracking Accelerometer and Gyroscope"
        }
        charger = {
            "reference": "U4",
            "mpn": "TP4056",
            "lib_id": "Battery_Management:TP4056",
            "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "role": "1A Standalone Linear LiPo Battery Charger with Thermal Regulation"
        }
        return {
            "project_name": "Environmental_Sensor_IoT_Node",
            "archetype": "sensor_iot",
            "mcu": mcu,
            "components": [mcu, sensor_env, sensor_imu, charger],
            "nets": [
                {"net": "GND", "type": "power"},
                {"net": "+3V3", "type": "power"},
                {"net": "VBAT", "type": "power"},
                {"net": "I2C_SDA", "type": "signal"},
                {"net": "I2C_SCL", "type": "signal"},
            ],
            "board_dims": (55.0, 40.0),
            "rules": {"trace_width_power_mm": 0.4, "trace_width_signal_mm": 0.2}
        }

    def _build_rp2040_audio_architecture(self) -> Dict[str, Any]:
        mcu = {
            "reference": "U1",
            "mpn": "RP2040",
            "lib_id": "MCU_RaspberryPi:RP2040",
            "footprint": "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
            "supply_voltage": "3.3V"
        }
        dac = {
            "reference": "U2",
            "mpn": "PCM5102APWR",
            "lib_id": "Audio:PCM5102A",
            "footprint": "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
            "role": "32-Bit 384kHz Stereo Audio DAC with DirectPath Ground-Centered Output"
        }
        ldo = {
            "reference": "U3",
            "mpn": "TPS7A4700RGWR",
            "lib_id": "Regulator_Linear:TPS7A4700",
            "footprint": "Package_DFN_QFN:QFN-20-1EP_5x5mm_P0.65mm_EP3.1x3.1mm",
            "role": "Ultra-Low Noise (4.17 uVRMS) 1A RF LDO for High-End Audio"
        }
        return {
            "project_name": "RP2040_Audiophile_I2S_DAC",
            "archetype": "audio_dac",
            "mcu": mcu,
            "components": [mcu, dac, ldo],
            "nets": [
                {"net": "GND", "type": "power"},
                {"net": "+3V3_ANA", "type": "power"},
                {"net": "+3V3_DIG", "type": "power"},
                {"net": "I2S_BCLK", "type": "high_speed"},
                {"net": "I2S_LRCK", "type": "high_speed"},
                {"net": "I2S_DATA", "type": "high_speed"},
                {"net": "AUDIO_OUT_L", "type": "analog"},
                {"net": "AUDIO_OUT_R", "type": "analog"},
            ],
            "board_dims": (65.0, 42.0),
            "rules": {"trace_width_power_mm": 0.5, "trace_width_signal_mm": 0.2}
        }

    def _build_esp32_iot_architecture(self) -> Dict[str, Any]:
        mcu = {
            "reference": "U1",
            "mpn": "ESP32-S3-WROOM-1-N16R8",
            "lib_id": "RF_Module:ESP32-S3-WROOM-1",
            "footprint": "RF_Module:ESP32-S3-WROOM-1",
            "supply_voltage": "3.3V"
        }
        buck = {
            "reference": "U2",
            "mpn": "AMS1117-3.3",
            "lib_id": "Regulator_Linear:AMS1117-3.3",
            "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
            "role": "Linear 5V to 3.3V LDO regulator"
        }
        can = {
            "reference": "U3",
            "mpn": "SN65HVD230DR",
            "lib_id": "Interface_CAN_LIN:SN65HVD230",
            "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "role": "3.3V CAN-Bus Transceiver"
        }
        usb = {
            "reference": "J1",
            "mpn": "TYPE-C-31-M-12",
            "lib_id": "Connector:USB_C_Receptacle_USB2.0_16P",
            "footprint": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
            "role": "USB-C Connector"
        }
        return {
            "project_name": "ESP32_S3_Industrial_IoT_System",
            "archetype": "esp32_iot",
            "mcu": mcu,
            "components": [mcu, buck, can, usb],
            "nets": [
                {"net": "GND", "type": "power"},
                {"net": "+3V3", "type": "power"},
                {"net": "VBUS", "type": "power"},
                {"net": "USB_DP", "type": "diff_pair"},
                {"net": "USB_DN", "type": "diff_pair"},
                {"net": "CAN_TX", "type": "signal"},
                {"net": "CAN_RX", "type": "signal"},
                {"net": "CAN_H", "type": "diff_pair"},
                {"net": "CAN_L", "type": "diff_pair"},
            ],
            "board_dims": (75.0, 45.0),
            "rules": {"trace_width_power_mm": 0.5, "trace_width_signal_mm": 0.2}
        }
