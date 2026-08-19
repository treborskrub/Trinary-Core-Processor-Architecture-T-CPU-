
import numpy as np
from enum import IntEnum

class TrinaryLogic(IntEnum):
    RELEVANT = 1      # Wave Crest (+1)   -> Active Value
    UNKNOWN = 0       # Ground Neutral (0) -> Structural Data Absence
    IRRELEVANT = -1   # Wave Trough (-1)   -> Path Void / Early Exit Trigger

class TrinaryProcessor:
    """
    Emulates a 14-node Balanced Ternary Processor.
    Operates natively on vectors of (-1, 0, +1) using wave-domain operations.
    """
    def __init__(self, num_nodes: int = 14):
        self.num_nodes = num_nodes
        # Registers: Each holds a 14-node ternary wavefront array
        self.registers = {
            "R1": np.zeros(self.num_nodes),  # General Purpose 1
            "R2": np.zeros(self.num_nodes),  # General Purpose 2
            "ACC": np.zeros(self.num_nodes), # Wavefront Accumulator
            "SR": 0                          # Status Register (Global State Context)
        }
        # Sieve Hardware Integration for pipeline security
        self.phi = 1.61803398875
        self.sieve_threshold = np.pi * self.phi * (1.0 / 3.0)
        self.lambda_max = 1.35

    def load_register(self, reg_name: str, wave_vector: np.ndarray):
        """Loads an input wavefront directly into the processor registers."""
        if len(wave_vector) != self.num_nodes:
            raise ValueError(f"Vector must precisely match the {self.num_nodes}-node fabric grid.")
        self.registers[reg_name] = np.copy(wave_vector)

    def execute_and(self, src_reg1: str, src_reg2: str, dest_reg: str):
        """
        Trinary AND (Strict Filter Fallback Logic):
        Applies element-wise min(). Irrelevant (-1) wins over everything.
        """
        v1 = self.registers[src_reg1]
        v2 = self.registers[src_reg2]
        self.registers[dest_reg] = np.minimum(v1, v2)
        self._update_status_register(dest_reg)

    def execute_or(self, src_reg1: str, src_reg2: str, dest_reg: str):
        """
        Trinary OR (Relevance Priority Logic):
        Applies element-wise max(). Relevant (+1) wins over everything.
        """
        v1 = self.registers[src_reg1]
        v2 = self.registers[src_reg2]
        self.registers[dest_reg] = np.maximum(v1, v2)
        self._update_status_register(dest_reg)

    def execute_refract_rotation(self, src_reg: str, dest_reg: str):
        """
        Executes a hardware-level spatial refraction cycle.
        Applies the Pi-Phi-1/3 arrangement loop.
        """
        state = np.copy(self.registers[src_reg])
        rotation_matrix = np.roll(state, 1) * (1.0 / 3.0)
        
        # Wavefront propagation
        new_state = (state * np.cos(self.sieve_threshold)) + (rotation_matrix * np.sin(self.sieve_threshold))
        
        # Enforce Shortfall Constraints: Snap back to ternary limits to avoid floating overflow
        self.registers[dest_reg] = np.clip(np.round(new_state), -1.0, 1.0)
        self._update_status_register(dest_reg)

    def _update_status_register(self, monitored_reg: str):
        """
        Updates the processor status using Early-Exit Logic rules.
        If a register drops entirely into the VOID state (-1), status sets a hardware halt.
        """
        target_vector = self.registers[monitored_reg]
        if np.min(target_vector) == TrinaryLogic.IRRELEVANT and np.max(target_vector) <= 0.0:
            self.registers["SR"] = int(TrinaryLogic.IRRELEVANT)  # VOIDED BRANCH SIGNIFIED
        elif np.all(target_vector == 0.0):
            self.registers["SR"] = int(TrinaryLogic.UNKNOWN)     # UNMAPPED STANDBY SIGNIFIED
        else:
            self.registers["SR"] = int(TrinaryLogic.RELEVANT)    # ACTIVE SYSTEM HEALTHY

# Hardware Sandbox Verification
if __name__ == "__main__":
    t_cpu = TrinaryProcessor()
    
    # Simulate a stream package coming into R1
    package_r1 = np.array([1., 0., 1., 1., 0., -1., 0., 1., -1., 0., 0., 1., 1., 0.])
    # Simulate a masking filter in R2
    mask_r2    = np.array([1., 1., 1., 1., 1., -1., 1., 1., -1., 1., 1., 1., 1., 1.])
    
    t_cpu.load_register("R1", package_r1)
    t_cpu.load_register("R2", mask_r2)
    
    print("Executing Strict AND Filtering into Accumulator...")
    t_cpu.execute_and("R1", "R2", "ACC")
    print(f"Accumulator Vector  : {t_cpu.registers['ACC']}")
    print(f"Hardware Status Code: {t_cpu.registers['SR']} (Status: {TrinaryLogic(t_cpu.registers['SR']).name})")
