"""
PIPO Multi-Stage Data Buffer & Throughput Simulator (EC2201 Syllabus)
Manages multi-stage parallel registers configured as a high-speed data buffer pipeline.
Calculates real-world performance metrics: Throughput, Latency, Bandwidth Efficiency, and Occupancy.
"""

from typing import List, Dict, Any, Optional
import time
from pipo_register import PIPORegister


class PIPODataBuffer:
    """
    Multi-stage PIPO Data Buffer pipeline with configurable buffer depth and bit width.
    """
    def __init__(self, depth: int = 8, bit_width: int = 8, clk_freq_mhz: float = 100.0):
        self.depth = depth
        self.bit_width = bit_width
        self.clk_freq_mhz = clk_freq_mhz
        
        # Internal buffer stages using PIPO Registers
        self.registers = [PIPORegister(bit_width=bit_width) for _ in range(depth)]
        self.buffer_data: List[Optional[int]] = [None] * depth
        
        self.write_ptr: int = 0
        self.read_ptr: int = 0
        self.count: int = 0
        
        self.total_clock_cycles: int = 0
        self.total_words_written: int = 0
        self.total_words_read: int = 0
        self.overflow_events: int = 0
        self.underflow_events: int = 0
        
        self.entry_timestamps: Dict[int, int] = {}  # word_id -> clock_cycle
        self.latencies: List[int] = []
        self.history: List[Dict[str, Any]] = []

    def is_full(self) -> bool:
        return self.count == self.depth

    def is_empty(self) -> bool:
        return self.count == 0

    def step_clock(self, 
                   write_enable: int = 0, 
                   read_enable: int = 0, 
                   write_word: Optional[int] = None, 
                   reset_n: int = 1) -> Dict[str, Any]:
        """
        Executes a single system clock cycle (Rising Edge).
        """
        self.total_clock_cycles += 1
        current_cycle = self.total_clock_cycles
        
        write_occurred = False
        read_occurred = False
        read_word_val: Optional[int] = None
        status_msg = "Idle"

        # Asynchronous Reset
        if not reset_n:
            self.buffer_data = [None] * self.depth
            self.write_ptr = 0
            self.read_ptr = 0
            self.count = 0
            self.entry_timestamps.clear()
            for r in self.registers:
                r.clock_step(clk=0, d_bus=[0]*self.bit_width, reset_n=0)
                r.clock_step(clk=1, d_bus=[0]*self.bit_width, reset_n=0)
            status_msg = "Buffer Reset"
        else:
            # 1. Handle Read Operation on Clock Pulse
            if read_enable:
                if self.is_empty():
                    self.underflow_events += 1
                    status_msg = "Underflow Error (Read empty buffer)"
                else:
                    read_word_val = self.buffer_data[self.read_ptr]
                    # Simulate reading from PIPO register at read_ptr
                    reg = self.registers[self.read_ptr]
                    reg_out = reg.get_state()["q_int"]
                    
                    self.buffer_data[self.read_ptr] = None
                    self.read_ptr = (self.read_ptr + 1) % self.depth
                    self.count -= 1
                    self.total_words_read += 1
                    read_occurred = True
                    
                    # Calculate latency
                    if self.total_words_read in self.entry_timestamps:
                        entry_cycle = self.entry_timestamps.pop(self.total_words_read)
                        latency_cycles = current_cycle - entry_cycle
                        self.latencies.append(latency_cycles)
                    status_msg = f"Read word 0x{read_word_val:02X}"

            # 2. Handle Write Operation on Clock Pulse
            if write_enable and write_word is not None:
                if self.is_full():
                    self.overflow_events += 1
                    status_msg = "Overflow Error (Write full buffer)"
                else:
                    # Convert integer to bit list
                    d_bus = [(write_word >> i) & 1 for i in range(self.bit_width)]
                    
                    # Clock low -> high pulse into target PIPO register
                    reg = self.registers[self.write_ptr]
                    reg.clock_step(clk=0, d_bus=d_bus, load=1, reset_n=1, oe=1)
                    reg.clock_step(clk=1, d_bus=d_bus, load=1, reset_n=1, oe=1)
                    
                    self.buffer_data[self.write_ptr] = write_word & ((1 << self.bit_width) - 1)
                    self.write_ptr = (self.write_ptr + 1) % self.depth
                    self.count += 1
                    self.total_words_written += 1
                    write_occurred = True
                    
                    self.entry_timestamps[self.total_words_written] = current_cycle
                    if status_msg == "Idle" or "Read" in status_msg:
                        status_msg += f" | Wrote word 0x{write_word:02X}"

        # Metrics snapshot
        words_per_cycle = self.total_words_read / self.total_clock_cycles if self.total_clock_cycles > 0 else 0
        bit_rate_mbps = words_per_cycle * self.bit_width * self.clk_freq_mhz
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

        step_record = {
            "cycle": current_cycle,
            "reset_n": reset_n,
            "write_enable": write_enable,
            "read_enable": read_enable,
            "write_word": write_word,
            "read_word": read_word_val,
            "buffer_count": self.count,
            "is_full": self.is_full(),
            "is_empty": self.is_empty(),
            "buffer_contents": list(self.buffer_data),
            "status": status_msg,
            "words_per_cycle": round(words_per_cycle, 4),
            "bit_rate_mbps": round(bit_rate_mbps, 2),
            "avg_latency_cycles": round(avg_latency, 2),
            "overflow_events": self.overflow_events,
            "underflow_events": self.underflow_events
        }
        self.history.append(step_record)
        return step_record

    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculates global performance metrics for the simulator run."""
        words_per_cycle = self.total_words_read / self.total_clock_cycles if self.total_clock_cycles > 0 else 0
        bit_rate_mbps = words_per_cycle * self.bit_width * self.clk_freq_mhz
        max_possible_mbps = self.bit_width * self.clk_freq_mhz
        efficiency_pct = (bit_rate_mbps / max_possible_mbps * 100.0) if max_possible_mbps > 0 else 0.0
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

        return {
            "total_cycles": self.total_clock_cycles,
            "words_written": self.total_words_written,
            "words_read": self.total_words_read,
            "overflow_count": self.overflow_events,
            "underflow_count": self.underflow_events,
            "throughput_words_per_cycle": round(words_per_cycle, 4),
            "bandwidth_mbps": round(bit_rate_mbps, 2),
            "max_bandwidth_mbps": round(max_possible_mbps, 2),
            "bandwidth_efficiency_pct": round(efficiency_pct, 2),
            "avg_latency_cycles": round(avg_latency, 2),
            "buffer_depth": self.depth,
            "bit_width": self.bit_width
        }


if __name__ == "__main__":
    print("Testing PIPO Multi-Stage Data Buffer Simulator...")
    buf = PIPODataBuffer(depth=4, bit_width=8, clk_freq_mhz=100.0)
    
    # Write 4 words
    test_words = [0x11, 0x22, 0x33, 0x44]
    for w in test_words:
        rec = buf.step_clock(write_enable=1, read_enable=0, write_word=w)
        print(f"Cycle {rec['cycle']}: Count={rec['buffer_count']} | Contents={rec['buffer_contents']}")

    # Read 4 words back
    for _ in range(4):
        rec = buf.step_clock(write_enable=0, read_enable=1)
        print(f"Cycle {rec['cycle']}: Read=0x{rec['read_word']:02X} | Count={rec['buffer_count']}")

    print("\nPerformance Summary:")
    print(buf.get_performance_summary())
