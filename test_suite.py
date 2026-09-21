"""
Comprehensive Test Suite for PIPO Data Buffer Simulator (EC2201 Syllabus)
Executes 10 Normal Test Cases + 5 Edge/Fault Test Cases.
Validates digital logic behavior, truth table compliance, timing violations, and error handling.
"""

from typing import List, Dict, Any
import pandas as pd
from pipo_register import PIPORegister
from buffer_simulator import PIPODataBuffer


class PIPOTestSuite:
    """
    Automated Test Runner for 15 PIPO Register & Buffer Test Cases.
    """
    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> pd.DataFrame:
        self.results.clear()
        
        # --- NORMAL TEST CASES (1-10) ---
        self._test_tc01_single_word_parallel_load()
        self._test_tc02_multi_word_sequential_burst()
        self._test_tc03_clock_enable_disabled()
        self._test_tc04_asynchronous_reset()
        self._test_tc05_tristate_output_enable()
        self._test_tc06_varying_bit_width_4bit()
        self._test_tc07_varying_bit_width_16bit()
        self._test_tc08_varying_bit_width_32bit()
        self._test_tc09_full_buffer_pipeline_fill()
        self._test_tc10_back_to_back_simultaneous_read_write()

        # --- EDGE / FAULT TEST CASES (11-15) ---
        self._test_tc11_setup_time_violation_fault()
        self._test_tc12_hold_time_violation_fault()
        self._test_tc13_reset_during_active_write_pulse()
        self._test_tc14_buffer_overflow_fault()
        self._test_tc15_buffer_underflow_fault()

        return pd.DataFrame(self.results)

    def _add_result(self, tc_id: str, name: str, category: str, passed: bool, details: str, truth_table_op: str):
        self.results.append({
            "TC_ID": tc_id,
            "Test Name": name,
            "Category": category,
            "Status": "PASS" if passed else "FAIL",
            "Truth Table Operation": truth_table_op,
            "Details": details
        })

    def _test_tc01_single_word_parallel_load(self):
        reg = PIPORegister(bit_width=8)
        d_in = [1, 0, 1, 0, 1, 0, 1, 0]  # 0x55
        reg.clock_step(clk=0, d_bus=d_in, load=1, reset_n=1, oe=1)
        st = reg.clock_step(clk=1, d_bus=d_in, load=1, reset_n=1, oe=1)
        passed = (st["q_int"] == 0x55 and st["q_bus_output"] == d_in)
        self._add_result("TC01", "Single Word Parallel Load & Read", "Normal", passed,
                         f"Loaded 0x55 -> Output: {st['q_hex']}", "Parallel Data Load")

    def _test_tc02_multi_word_sequential_burst(self):
        buf = PIPODataBuffer(depth=8, bit_width=8)
        words = [0x10, 0x20, 0x30, 0x40]
        for w in words:
            buf.step_clock(write_enable=1, read_enable=0, write_word=w)
        
        read_back = []
        for _ in range(4):
            rec = buf.step_clock(write_enable=0, read_enable=1)
            read_back.append(rec["read_word"])
            
        passed = (words == read_back)
        self._add_result("TC02", "Multi-Word Sequential Burst Write/Read", "Normal", passed,
                         f"Sent {[hex(w) for w in words]}, Received {[hex(r) for r in read_back]}", "Parallel FIFO Transfer")

    def _test_tc03_clock_enable_disabled(self):
        reg = PIPORegister(bit_width=8)
        # First load 0xAA
        reg.clock_step(clk=0, d_bus=[0,1,0,1,0,1,0,1], load=1, reset_n=1)
        reg.clock_step(clk=1, d_bus=[0,1,0,1,0,1,0,1], load=1, reset_n=1)
        # Attempt to write 0xFF with LOAD=0
        reg.clock_step(clk=0, d_bus=[1]*8, load=0, reset_n=1)
        st = reg.clock_step(clk=1, d_bus=[1]*8, load=0, reset_n=1)
        passed = (st["q_int"] == 0xAA)  # output preserved at 0xAA
        self._add_result("TC03", "Clock Enable (LOAD=0) Inhibit Test", "Normal", passed,
                         f"Presented 0xFF with LOAD=0 -> Register held 0xAA", "Clock Disabled (Hold)")

    def _test_tc04_asynchronous_reset(self):
        reg = PIPORegister(bit_width=8)
        # Load 0xFF
        reg.clock_step(clk=0, d_bus=[1]*8, load=1, reset_n=1)
        reg.clock_step(clk=1, d_bus=[1]*8, load=1, reset_n=1)
        # Assert active low reset
        st = reg.clock_step(clk=1, d_bus=[1]*8, load=1, reset_n=0)
        passed = (st["q_int"] == 0 and st["d_bus_int"] == 255)
        self._add_result("TC04", "Asynchronous Reset (RST_N=0)", "Normal", passed,
                         f"Asserted RST_N=0 -> Register cleared to 0x00 immediately", "Asynchronous Reset")

    def _test_tc05_tristate_output_enable(self):
        reg = PIPORegister(bit_width=8)
        reg.clock_step(clk=0, d_bus=[1,1,0,0,1,1,0,0], load=1, reset_n=1, oe=1)  # 0x33
        reg.clock_step(clk=1, d_bus=[1,1,0,0,1,1,0,0], load=1, reset_n=1, oe=1)
        # Disable output OE=0
        st = reg.clock_step(clk=1, d_bus=[1,1,0,0,1,1,0,0], load=1, reset_n=1, oe=0)
        passed = (st["q_int"] == 0x33 and st["q_bus_output"] is None)
        self._add_result("TC05", "Tri-State Output Enable (OE=0)", "Normal", passed,
                         f"Set OE=0 -> Internal Q=0x33 preserved, Bus Output=Hi-Z (None)", "Output Disabled (Hi-Z)")

    def _test_tc06_varying_bit_width_4bit(self):
        reg = PIPORegister(bit_width=4)
        reg.clock_step(clk=0, d_bus=[1,1,1,1], load=1, reset_n=1)
        st = reg.clock_step(clk=1, d_bus=[1,1,1,1], load=1, reset_n=1)
        passed = (st["q_int"] == 0x0F)
        self._add_result("TC06", "4-Bit PIPO Register Load", "Normal", passed,
                         f"4-bit load 0x0F -> Output: {st['q_hex']}", "Parallel Data Load")

    def _test_tc07_varying_bit_width_16bit(self):
        reg = PIPORegister(bit_width=16)
        d_16 = [(0xABCD >> i) & 1 for i in range(16)]
        reg.clock_step(clk=0, d_bus=d_16, load=1, reset_n=1)
        st = reg.clock_step(clk=1, d_bus=d_16, load=1, reset_n=1)
        passed = (st["q_int"] == 0xABCD)
        self._add_result("TC07", "16-Bit PIPO Register Load", "Normal", passed,
                         f"16-bit load 0xABCD -> Output: {st['q_hex']}", "Parallel Data Load")

    def _test_tc08_varying_bit_width_32bit(self):
        reg = PIPORegister(bit_width=32)
        val = 0xDEADBEEF
        d_32 = [(val >> i) & 1 for i in range(32)]
        reg.clock_step(clk=0, d_bus=d_32, load=1, reset_n=1)
        st = reg.clock_step(clk=1, d_bus=d_32, load=1, reset_n=1)
        passed = (st["q_int"] == val)
        self._add_result("TC08", "32-Bit PIPO Register Load", "Normal", passed,
                         f"32-bit load 0xDEADBEEF -> Output: {st['q_hex']}", "Parallel Data Load")

    def _test_tc09_full_buffer_pipeline_fill(self):
        buf = PIPODataBuffer(depth=4, bit_width=8)
        for i in range(4):
            buf.step_clock(write_enable=1, read_enable=0, write_word=0x10 + i)
        summary = buf.get_performance_summary()
        passed = (buf.is_full() and summary["words_written"] == 4)
        self._add_result("TC09", "Full Buffer Pipeline Fill", "Normal", passed,
                         f"Filled 4/4 slots -> Buffer FULL flag = True", "Pipeline Occupancy")

    def _test_tc10_back_to_back_simultaneous_read_write(self):
        buf = PIPODataBuffer(depth=4, bit_width=8)
        # Fill 2 words first
        buf.step_clock(write_enable=1, write_word=0xA1)
        buf.step_clock(write_enable=1, write_word=0xA2)
        # Simultaneous read and write
        rec = buf.step_clock(write_enable=1, read_enable=1, write_word=0xA3)
        passed = (rec["read_word"] == 0xA1 and rec["buffer_count"] == 2)
        self._add_result("TC10", "Simultaneous Back-to-Back Read/Write", "Normal", passed,
                         f"Read 0xA1 while writing 0xA3 -> Count stable at 2", "Concurrent Access")

    def _test_tc11_setup_time_violation_fault(self):
        reg = PIPORegister(bit_width=8, t_su=1.0)
        # Data changes at t=9.5 ns, clock rises at t=10.0 ns (delta = 0.5 ns < t_su = 1.0 ns)
        reg.clock_step(clk=0, d_bus=[1]*8, load=1, reset_n=1, current_time=9.5)
        st = reg.clock_step(clk=1, d_bus=[1]*8, load=1, reset_n=1, current_time=10.0)
        passed = st["setup_violation"] and st["metastable"]
        self._add_result("TC11", "Setup Time Violation Fault Injection", "Edge/Fault", passed,
                         f"Input changed 0.5ns before CLK (t_su=1.0ns) -> Setup Violation & Metastability flagged", "Timing Fault")

    def _test_tc12_hold_time_violation_fault(self):
        reg = PIPORegister(bit_width=8, t_h=0.5)
        # Clock rises at t=10.0 ns
        reg.clock_step(clk=0, d_bus=[0]*8, load=1, reset_n=1, current_time=0.0)
        reg.clock_step(clk=1, d_bus=[0]*8, load=1, reset_n=1, current_time=10.0)
        # Input changes at t=10.2 ns (delta = 0.2 ns < t_h = 0.5 ns)
        st = reg.clock_step(clk=1, d_bus=[1]*8, load=1, reset_n=1, current_time=10.2)
        passed = st["hold_violation"]
        self._add_result("TC12", "Hold Time Violation Fault Injection", "Edge/Fault", passed,
                         f"Input toggled 0.2ns after CLK edge (t_h=0.5ns) -> Hold Violation flagged", "Timing Fault")

    def _test_tc13_reset_during_active_write_pulse(self):
        buf = PIPODataBuffer(depth=4, bit_width=8)
        # Assert reset_n=0 during write command
        rec = buf.step_clock(write_enable=1, read_enable=0, write_word=0x77, reset_n=0)
        passed = (rec["buffer_count"] == 0 and rec["status"] == "Buffer Reset")
        self._add_result("TC13", "Reset During Active Write Pulse", "Edge/Fault", passed,
                         f"Triggered RST_N=0 alongside Write Pulse -> Write aborted & Buffer cleared", "Asynchronous Override")

    def _test_tc14_buffer_overflow_fault(self):
        buf = PIPODataBuffer(depth=2, bit_width=8)
        buf.step_clock(write_enable=1, write_word=0x01)
        buf.step_clock(write_enable=1, write_word=0x02)
        # Overflow write attempt
        rec = buf.step_clock(write_enable=1, write_word=0x03)
        passed = (rec["overflow_events"] == 1 and "Overflow Error" in rec["status"])
        self._add_result("TC14", "Buffer Overflow Fault Injection", "Edge/Fault", passed,
                         f"Attempted 3rd write on depth=2 buffer -> Overflow Event detected", "Capacity Overflow Fault")

    def _test_tc15_buffer_underflow_fault(self):
        buf = PIPODataBuffer(depth=2, bit_width=8)
        # Underflow read attempt from empty buffer
        rec = buf.step_clock(write_enable=0, read_enable=1)
        passed = (rec["underflow_events"] == 1 and "Underflow Error" in rec["status"])
        self._add_result("TC15", "Buffer Underflow Fault Injection", "Edge/Fault", passed,
                         f"Attempted read from empty buffer -> Underflow Event detected", "Capacity Underflow Fault")


if __name__ == "__main__":
    print("Executing PIPO Data Buffer Test Suite (15 Test Cases)...")
    runner = PIPOTestSuite()
    df_results = runner.run_all_tests()
    print(df_results.to_string(index=False))
    
    total_pass = (df_results["Status"] == "PASS").sum()
    print(f"\nTest Summary: {total_pass} / {len(df_results)} Passed.")
