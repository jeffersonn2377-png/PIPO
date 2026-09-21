"""
PIPO Register Hardware Model (EC2201 Digital Electronics Syllabus)
Implements hardware-level Parallel-In Parallel-Out (PIPO) data register using D Flip-Flops.
Supports timing parameters (setup/hold time, propagation delay), Clock Enable, Asynchronous Reset,
and Tri-state Output Enable.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd


class DFlipFlop:
    """
    Hardware-accurate positive edge-triggered D Flip-Flop model with timing constraint checking.
    """
    def __init__(self, bit_id: int = 0, t_su: float = 1.0, t_h: float = 0.5, t_pd: float = 2.0):
        self.bit_id = bit_id
        self.t_su = t_su  # Setup time in ns
        self.t_h = t_h    # Hold time in ns
        self.t_pd = t_pd  # Propagation delay in ns
        
        self.q: int = 0
        self.q_bar: int = 1
        self.last_d: int = 0
        self.last_d_change_time: float = -100.0
        self.last_clk_time: float = -100.0
        
        self.setup_violation: bool = False
        self.hold_violation: bool = False
        self.is_metastable: bool = False

    def update_d(self, d_val: int, current_time: float):
        """Update D input signal and record time for timing checks."""
        d_val = 1 if d_val else 0
        if d_val != self.last_d:
            self.last_d = d_val
            self.last_d_change_time = current_time

    def trigger_clock(self, clk_rising_edge: bool, reset_n: bool, enable: bool, current_time: float) -> Tuple[int, Dict[str, Any]]:
        """
        Processes clock transition or asynchronous reset.
        Returns (Q_output, status_dict)
        """
        status = {
            "setup_violation": False,
            "hold_violation": False,
            "metastable": False,
            "reset_applied": False,
            "enabled": enable
        }

        # Asynchronous Active-Low Reset
        if not reset_n:
            self.q = 0
            self.q_bar = 1
            self.setup_violation = False
            self.hold_violation = False
            self.is_metastable = False
            status["reset_applied"] = True
            return self.q, status

        # On Rising Clock Edge
        if clk_rising_edge:
            self.last_clk_time = current_time
            
            # Setup Time Check: D must be stable for t_su before clock edge
            time_since_d_change = current_time - self.last_d_change_time
            if 0 <= time_since_d_change < self.t_su:
                self.setup_violation = True
                status["setup_violation"] = True
                # Setup violation causes potential metastability
                self.is_metastable = True
                status["metastable"] = True

            # Clock Enable Check
            if enable:
                if self.is_metastable:
                    # Deterministic glitch simulation under metastability (unknown or flipped state)
                    self.q = 1 - self.last_d
                else:
                    self.q = self.last_d
                self.q_bar = 1 - self.q

        # Hold Time Check: D must remain stable for t_h after clock edge
        time_since_clk = current_time - self.last_clk_time
        if 0 < time_since_clk < self.t_h and current_time == self.last_d_change_time:
            self.hold_violation = True
            status["hold_violation"] = True

        return self.q, status


class PIPORegister:
    """
    N-bit Parallel-In Parallel-Out (PIPO) Data Register consisting of N D-Flip-Flops.
    Inputs: Data Input Bus D[N-1:0], Clock (CLK), Load Enable (LOAD), Reset Active Low (RST_N), Output Enable (OE).
    Outputs: Parallel Data Output Bus Q[N-1:0] (Tri-stated if OE is False).
    """
    def __init__(self, bit_width: int = 8, t_su: float = 1.0, t_h: float = 0.5, t_pd: float = 2.0):
        self.bit_width = bit_width
        self.flip_flops = [DFlipFlop(i, t_su, t_h, t_pd) for i in range(bit_width)]
        self.last_clk = 0
        self.oe = True
        self.current_q = [0] * bit_width
        self.bus_output: Optional[List[int]] = [0] * bit_width
        self.sim_time: float = 0.0
        self.history: List[Dict[str, Any]] = []

    def clock_step(self, 
                   clk: int, 
                   d_bus: List[int], 
                   load: int = 1, 
                   reset_n: int = 1, 
                   oe: int = 1, 
                   current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Simulates a single clock step or state update for the PIPO Register.
        """
        if current_time is None or current_time <= 0.0:
            self.sim_time += 5.0
            current_time = self.sim_time
        # Format D inputs to N-bits
        d_clean = [1 if bit else 0 for bit in d_bus[:self.bit_width]]
        if len(d_clean) < self.bit_width:
            d_clean += [0] * (self.bit_width - len(d_clean))

        clk_val = 1 if clk else 0
        clk_rising_edge = (self.last_clk == 0 and clk_val == 1)
        self.last_clk = clk_val
        self.oe = bool(oe)

        # Update inputs and evaluate flip flops
        q_new = []
        any_setup_violation = False
        any_hold_violation = False
        any_metastable = False

        for i, ff in enumerate(self.flip_flops):
            ff.update_d(d_clean[i], current_time)
            q_bit, status = ff.trigger_clock(
                clk_rising_edge=clk_rising_edge,
                reset_n=bool(reset_n),
                enable=bool(load),
                current_time=current_time
            )
            q_new.append(q_bit)
            if status["setup_violation"]:
                any_setup_violation = True
            if status["hold_violation"]:
                any_hold_violation = True
            if status["metastable"]:
                any_metastable = True

        self.current_q = q_new
        
        # Tri-state buffer output
        if self.oe:
            self.bus_output = list(self.current_q)
        else:
            self.bus_output = None  # High Impedance (Hi-Z)

        # Calculate integer word value
        int_val = sum(bit << i for i, bit in enumerate(self.current_q))
        hex_val = f"0x{int_val:0{(self.bit_width + 3) // 4}X}"
        bin_val = "".join(str(b) for b in reversed(self.current_q))

        state_record = {
            "time_ns": current_time,
            "clk": clk_val,
            "reset_n": reset_n,
            "load": load,
            "oe": oe,
            "d_bus_bin": "".join(str(b) for b in reversed(d_clean)),
            "d_bus_int": sum(b << i for i, b in enumerate(d_clean)),
            "q_bin": bin_val,
            "q_int": int_val,
            "q_hex": hex_val,
            "q_bus_output": self.bus_output,
            "setup_violation": any_setup_violation,
            "hold_violation": any_hold_violation,
            "metastable": any_metastable
        }
        self.history.append(state_record)
        return state_record

    def get_state(self) -> Dict[str, Any]:
        """Returns current register state."""
        int_val = sum(bit << i for i, bit in enumerate(self.current_q))
        return {
            "bit_width": self.bit_width,
            "q_bits": self.current_q,
            "q_int": int_val,
            "q_hex": f"0x{int_val:0{(self.bit_width + 3) // 4}X}",
            "q_bin": "".join(str(b) for b in reversed(self.current_q)),
            "oe": self.oe,
            "bus_output": self.bus_output
        }

    @staticmethod
    def generate_truth_table(bit_width: int = 4) -> pd.DataFrame:
        """
        Generates truth table for a PIPO register demonstrating operation.
        """
        rows = []
        # Case 1: Reset Active
        rows.append({
            "CLK": "X", "RST_N": 0, "LOAD": "X", "OE": 1,
            "D_In": "X", "Q(t+1)": "0" * bit_width, "Output Bus": "0" * bit_width, "Operation": "Asynchronous Reset"
        })
        # Case 2: Clock Low / No Edge
        rows.append({
            "CLK": "0", "RST_N": 1, "LOAD": 1, "OE": 1,
            "D_In": "Data", "Q(t+1)": "Q(t) (No Change)", "Output Bus": "Q(t)", "Operation": "Hold / Memory State"
        })
        # Case 3: Clock High / No Edge
        rows.append({
            "CLK": "1", "RST_N": 1, "LOAD": 1, "OE": 1,
            "D_In": "Data", "Q(t+1)": "Q(t) (No Change)", "Output Bus": "Q(t)", "Operation": "Hold / Memory State"
        })
        # Case 4: Rising Edge with LOAD = 0
        rows.append({
            "CLK": "RISING", "RST_N": 1, "LOAD": 0, "OE": 1,
            "D_In": "Data", "Q(t+1)": "Q(t) (Disabled)", "Output Bus": "Q(t)", "Operation": "Clock Disabled (Hold)"
        })
        # Case 5: Rising Edge with LOAD = 1
        rows.append({
            "CLK": "RISING", "RST_N": 1, "LOAD": 1, "OE": 1,
            "D_In": "Data (Parallel In)", "Q(t+1)": "Data (Parallel Out)", "Output Bus": "Data", "Operation": "Parallel Data Load"
        })
        # Case 6: Tri-state OE = 0
        rows.append({
            "CLK": "RISING", "RST_N": 1, "LOAD": 1, "OE": 0,
            "D_In": "Data", "Q(t+1)": "Data", "Output Bus": "Hi-Z (High Impedance)", "Operation": "Output Disabled (Hi-Z)"
        })

        return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Testing PIPO Register Hardware Model...")
    pipo = PIPORegister(bit_width=8)
    
    # Test parallel load 0xA5 = 10100101
    d_input = [1, 0, 1, 0, 0, 1, 0, 1]
    
    # Clock low
    st1 = pipo.clock_step(clk=0, d_bus=d_input, load=1, reset_n=1, oe=1, current_time=0.0)
    print("CLK=0 State:", st1["q_hex"], "| Output:", st1["q_bus_output"])
    
    # Clock rising edge
    st2 = pipo.clock_step(clk=1, d_bus=d_input, load=1, reset_n=1, oe=1, current_time=5.0)
    print("CLK=1 (Rising Edge) State:", st2["q_hex"], "| Output:", st2["q_bus_output"])
    
    print("\nTruth Table preview:")
    print(PIPORegister.generate_truth_table(4).to_string())
