
import numpy as np
import time
from typing import Dict, List, Callable

# =====================================================================
# 1. TRINARY STATE DEFINITIONS
# =====================================================================
class TrinaryLogic:
    RELEVANT = 1      # Wave Crest (+1)   -> Active Value
    UNKNOWN = 0       # Ground Neutral (0) -> Structural Data Absence
    IRRELEVANT = -1   # Wave Trough (-1)   -> Path Void / Early Exit Trigger

# =====================================================================
# 2. HARDWARE EMULATOR MODULE: T-CPU
# =====================================================================
class TrinaryProcessor:
    """
    Emulates a 14-node Balanced Ternary Processor.
    Operates natively on vectors of (-1, 0, +1) using wave-domain operations.
    """
    def __init__(self, num_nodes: int = 14):
        self.num_nodes = num_nodes
        self.registers = {
            "R1": np.zeros(self.num_nodes),
            "R2": np.zeros(self.num_nodes),
            "ACC": np.zeros(self.num_nodes),
            "SR": 0
        }
        self.phi = 1.61803398875
        self.sieve_threshold = np.pi * self.phi * (1.0 / 3.0)
        self.lambda_max = 1.35

    def load_register(self, reg_name: str, wave_vector: np.ndarray):
        if len(wave_vector) != self.num_nodes:
            raise ValueError(f"Vector must precisely match the {self.num_nodes}-node fabric grid.")
        self.registers[reg_name] = np.copy(wave_vector)

    def execute_and(self, src_reg1: str, src_reg2: str, dest_reg: str):
        v1 = self.registers[src_reg1]
        v2 = self.registers[src_reg2]
        self.registers[dest_reg] = np.minimum(v1, v2)
        self._update_status_register(dest_reg)

    def execute_or(self, src_reg1: str, src_reg2: str, dest_reg: str):
        v1 = self.registers[src_reg1]
        v2 = self.registers[src_reg2]
        self.registers[dest_reg] = np.maximum(v1, v2)
        self._update_status_register(dest_reg)

    def execute_refract_rotation(self, src_reg: str, dest_reg: str):
        state = np.copy(self.registers[src_reg])
        rotation_matrix = np.roll(state, 1) * (1.0 / 3.0)
        new_state = (state * np.cos(self.sieve_threshold)) + (rotation_matrix * np.sin(self.sieve_threshold))
        self.registers[dest_reg] = np.clip(np.round(new_state), -1.0, 1.0)
        self._update_status_register(dest_reg)

    def _update_status_register(self, monitored_reg: str):
        target_vector = self.registers[monitored_reg]
        if np.min(target_vector) == TrinaryLogic.IRRELEVANT and np.max(target_vector) <= 0.0:
            self.registers["SR"] = int(TrinaryLogic.IRRELEVANT)
        elif np.all(target_vector == 0.0):
            self.registers["SR"] = int(TrinaryLogic.UNKNOWN)
        else:
            self.registers["SR"] = int(TrinaryLogic.RELEVANT)

# =====================================================================
# 3. OPERATING SYSTEM KERNEL MODULE: T-OS
# =====================================================================
class TrinaryProcess:
    """Represents a native task running on TrinaryOS."""
    def __init__(self, pid: int, name: str, execution_vector: np.ndarray, ability_callback: Callable):
        self.pid = pid
        self.name = name
        self.vector = np.copy(execution_vector)
        self.ability_callback = ability_callback
        self.state = TrinaryLogic.UNKNOWN
        self.runtime_cycles = 0

class TrinaryOS:
    """The core operating system kernel."""
    def __init__(self, hardware_cpu: TrinaryProcessor):
        self.cpu = hardware_cpu
        self.process_table: Dict[int, TrinaryProcess] = {}
        self.next_pid = 100
        self.active_queue: List[int] = []
        self.shortfall_queue: List[int] = []
        self.void_queue: List[int] = []

    def register_ability(self, name: str, wavefront_signature: np.ndarray, callback: Callable) -> int:
        pid = self.next_pid
        process = TrinaryProcess(pid, name, wavefront_signature, callback)
        self.process_table[pid] = process
        self.next_pid += 1
        self._triage_process(process)
        return pid

    def _triage_process(self, process: TrinaryProcess):
        min_state = np.min(process.vector)
        max_state = np.max(process.vector)

        if min_state == TrinaryLogic.IRRELEVANT and max_state <= 0.0:
            process.state = TrinaryLogic.IRRELEVANT
            if process.pid not in self.void_queue:
                self.void_queue.append(process.pid)
            print(f"KERNEL: Task '{process.name}' [PID {process.pid}] -> VOID Queue (Purge Target).")
        elif np.all(process.vector == 0.0):
            process.state = TrinaryLogic.UNKNOWN
            if process.pid not in self.shortfall_queue:
                self.shortfall_queue.append(process.pid)
            print(f"KERNEL: Task '{process.name}' [PID {process.pid}] -> SHORTFALL Standby Queue.")
        else:
            process.state = TrinaryLogic.RELEVANT
            if process.pid not in self.active_queue:
                self.active_queue.append(process.pid)
            print(f"KERNEL: Task '{process.name}' [PID {process.pid}] -> ACTIVE Processing Queue.")

    def run_scheduler_cycle(self):
        print(f"\n--- OS Clock Tick: Executing Trinary Scheduler ---")

        # 1. Early-Exit Purge
        if self.void_queue:
            print(f"  [Early-Exit Engine] Instantly clearing {len(self.void_queue)} irrelevant threads.")
            for pid in list(self.void_queue):
                del self.process_table[pid]
                self.void_queue.remove(pid)

        # 2. Hardware Register Processing
        for pid in list(self.active_queue):
            proc = self.process_table[pid]
            self.cpu.load_register("R1", proc.vector)
            self.cpu.execute_refract_rotation("R1", "ACC")

            # Execute ability logic block
            proc.ability_callback(self.cpu.registers["ACC"])
            proc.runtime_cycles += 1
            proc.vector = np.copy(self.cpu.registers["ACC"])

            self.active_queue.remove(pid)
            self._triage_process(proc)
        print("--- End of Scheduler Cycle ---\n")

# =====================================================================
# 4. EXECUTION ENGINE SANDBOX RUN
# =====================================================================
if __name__ == "__main__":
    t_cpu = TrinaryProcessor()
    t_os = TrinaryOS(t_cpu)

    def ability_demo(wavefront):
        print(f"  -> Executing capability logic on wavefront context: {wavefront[:4]}")

    print("Registering System Tasks...")
    t_os.register_ability("TelemetryDecoder", np.array([1., 0., 1., 1., 0., -1., 0., 1., -1., 0., 0., 1., 1., 0.]), ability_demo)
    t_os.register_ability("ShortfallListener", np.zeros(14), ability_demo)
    t_os.register_ability("NoiseGhost", np.array([-1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1.]), ability_demo)

    t_os.run_scheduler_cycle()
