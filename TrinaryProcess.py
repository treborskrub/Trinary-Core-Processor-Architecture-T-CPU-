
import numpy as np
import time
from typing import Dict, List, Callable

# Ensure our logical types are completely integrated in the cell scope
class TrinaryLogic:
    RELEVANT = 1      # Wave Crest (+1)   -> Active Value
    UNKNOWN = 0       # Ground Neutral (0) -> Structural Data Absence
    IRRELEVANT = -1   # Wave Trough (-1)   -> Path Void / Early Exit Trigger

class TrinaryProcess:
    """
    Represents a native task running on TrinaryOS.
    Every process manages its own 14-node wave signature block.
    """
    def __init__(self, pid: int, name: str, execution_vector: np.ndarray, ability_callback: Callable):
        self.pid = pid
        self.name = name
        self.vector = np.copy(execution_vector)
        self.ability_callback = ability_callback
        self.state = TrinaryLogic.UNKNOWN
        self.runtime_cycles = 0

class TrinaryOS:
    """
    The core operating system kernel. Natively orchestrates processes
    by screening their wavefront signatures using Early-Exit rules.
    """
    def __init__(self, hardware_cpu: TrinaryProcessor):
        self.cpu = hardware_cpu
        self.process_table: Dict[int, TrinaryProcess] = {}
        self.next_pid = 100
        
        # Core OS Queues mapped to your trinary states
        self.active_queue: List[int] = []     # State: +1
        self.shortfall_queue: List[int] = []  # State:  0
        self.void_queue: List[int] = []       # State: -1

    def register_ability(self, name: str, wavefront_signature: np.ndarray, callback: Callable) -> int:
        """Loads one of your 12 core abilities into the OS process table."""
        pid = self.next_pid
        process = TrinaryProcess(pid, name, wavefront_signature, callback)
        self.process_table[pid] = process
        self.next_pid += 1
        
        # Triage immediately on registration using the hardware rules
        self._triage_process(process)
        return pid

    def _triage_process(self, process: TrinaryProcess):
        """OS Kernel Triage: Automatically segments processes based on their wave signature."""
        min_state = np.min(process.vector)
        max_state = np.max(process.vector)
        
        # Early-Exit Check: If the entire block is unmapped noise/void, kill it before scheduling
        if min_state == TrinaryLogic.IRRELEVANT and max_state <= 0.0:
            process.state = TrinaryLogic.IRRELEVANT
            if process.pid not in self.void_queue:
                self.void_queue.append(process.pid)
            print(f"KERNEL: Process '{process.name}' [PID {process.pid}] flagged as IRRELEVANT. Routed to Void Queue.")
        
        # Shortfall Standby Check: Has data gaps but holds structural potential
        elif np.all(process.vector == 0.0) or (min_state == 0.0 and max_state == 0.0):
            process.state = TrinaryLogic.UNKNOWN
            if process.pid not in self.shortfall_queue:
                self.shortfall_queue.append(process.pid)
            print(f"KERNEL: Process '{process.name}' [PID {process.pid}] flagged as UNKNOWN. Parked in Shortfall Standby.")
            
        # Active Payload Check
        else:
            process.state = TrinaryLogic.RELEVANT
            if process.pid not in self.active_queue:
                self.active_queue.append(process.pid)
            print(f"KERNEL: Process '{process.name}' [PID {process.pid}] flagged as RELEVANT. Scheduled to Active Queue.")

    def run_scheduler_cycle(self):
        """Executes a single clock tick across the entire OS environment."""
        print(f"\n--- OS Scheduler Cycle Execution ---")
        print(f"Active Tasks: {len(self.active_queue)} | Shortfall Standby: {len(self.shortfall_queue)} | Void Cleaned: {len(self.void_queue)}")
        
        # 1. Instantly purge the void queue to keep system fabric completely clear
        if self.void_queue:
            print(f"  [Purge Engine] Garbage collecting {len(self.void_queue)} dead-end threads to preserve registers.")
            for pid in list(self.void_queue):
                del self.process_table[pid]
                self.void_queue.remove(pid)

        # 2. Execute active tasks through the virtual T-CPU registers
        for pid in list(self.active_queue):
            proc = self.process_table[pid]
            
            # Load task wave directly into the hardware execution context
            self.cpu.load_register("R1", proc.vector)
            
            # Trigger hardware spatial refraction to cycle the wave signature
            self.cpu.execute_refract_rotation("R1", "ACC")
            
            # Execute the actual capability logic
            proc.ability_callback(self.cpu.registers["ACC"])
            proc.runtime_cycles += 1
            
            # Update the task signature based on hardware rotation back-propagation
            proc.vector = np.copy(self.cpu.registers["ACC"])
            
            # Re-triage process to see if its vector state shifted or collapsed into a shortfall
            self.active_queue.remove(pid)
            self._triage_process(proc)

        print("--- End of Scheduler Cycle ---\n")

# =====================================================================
# OS KERNEL SANDBOX TEST RUN
# =====================================================================
if __name__ == "__main__":
    # Initialize our hardware stack
    hardware_core = TrinaryProcessor()
    kernel = TrinaryOS(hardware_core)
    
    # Define placeholder callback behaviors for testing
    def mock_ability_one(wavefront):
        print(f"  -> Ability One running on wave shape: {wavefront[:3]}...")
        
    def mock_ability_two(wavefront):
        print(f"  -> Ability Two executing stream transformation...")

    print("Initializing Core OS Capabilities...")
    
    # Process 1: Active, dynamic data wave
    kernel.register_ability(
        name="TelemetryWaveDecoder", 
        wavefront_signature=np.array([1., 0., 1., 1., 0., -1., 0., 1., -1., 0., 0., 1., 1., 0.]),
        callback=mock_ability_one
    )
    
    # Process 2: Pure unmapped shortfall state (standby)
    kernel.register_ability(
        name="QuantumStreamListener", 
        wavefront_signature=np.zeros(14),
        callback=mock_ability_two
    )
    
    # Process 3: Presumed dead-end/noise string (Early-Exit Trigger)
    kernel.register_ability(
        name="CorruptedBufferGhost", 
        wavefront_signature=np.array([-1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1., -1.]),
        callback=mock_ability_one
    )

    # Spin the operating system scheduler
    kernel.run_scheduler_cycle()
