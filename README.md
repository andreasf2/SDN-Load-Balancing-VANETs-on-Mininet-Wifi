# SDN-Driven Load Balancing for V2I Networks (VANETs)

An advanced Software-Defined Networking (SDN) implementation designed to prevent network congestion, avoid hardware buffer overflows (Tail Drop), and ensure zero packet loss in Vehicle-to-Infrastructure (V2I) communication. Simulated and emulated using **Mininet-WiFi** and a custom **Ryu SDN Controller**.

## Project Overview

In traditional 802.11p (WAVE) vehicular networks, Access Points (APs) operate blindly. When multiple vehicles connect to a single AP, the CSMA/CA mechanism breaks down, leading to severe congestion, CPU exhaustion, and catastrophic packet loss. 

This project solves the congestion problem by decoupling the control plane from the data plane. By introducing a centralized **Ryu SDN Controller**, the network gains a "Global View". The controller actively monitors AP traffic and dynamically reroutes vehicles to underutilized access points before the hardware buffers overflow, achieving **seamless handover**.

## Tech Stack & Tools

* **Programming Language:** Python 3
* **SDN Controller:** Ryu
* **Network Emulator:** Mininet-WiFi (Linux Network Namespaces)
* **Protocols:** OpenFlow 1.3 (Control Plane), IEEE 802.11p (Wireless Medium), TCP/IP, ICMP
* **Testing & Traffic Generation:** iPerf, Ping

## Core Logic & Custom Implementation

Instead of relying on default load balancers, a custom Python logic was implemented inside the Ryu controller:

1. **Active Polling:** The controller polls the APs every `2 seconds` to monitor traffic volume. This interval acts as the optimal trade-off between network awareness and control plane overhead.
2. **Buffer Threshold Management:** A strict threshold of `50,000 Bytes (50KB)` was established. This preemptive limit ensures that traffic is redirected *before* the physical hardware queue fills up, effectively preventing Tail Drop.
3. **Dynamic Priority Rules:** Once the threshold is breached, the controller immediately pushes a new `FlowMod` rule via OpenFlow with **Priority 10**, granting "VIP access" to specific vehicles to seamlessly switch their traffic to the adjacent AP.

## Stress Testing & Results

To validate the architecture, the network was subjected to extreme stress tests designed to cripple a traditional topology:
* **ICMP Flooding:** Ping packets with a 1500-byte MTU payload to intentionally trigger IP Fragmentation and stress the AP's CPU.
* **TCP Saturation:** Continuous high-bandwidth TCP streams generated via `iPerf`.

### Key Achievements:
* **0% Packet Loss:** Even under extreme congestion, the SDN controller successfully rerouted traffic without dropping a single packet.
* **Seamless Handover:** The RTT (Round Trip Time) remained stable under `< 3ms` during the vehicle's transition between APs.


### System Logs Demo
When AP1 reaches the critical 50KB threshold, the controller intercepts the congestion:
> `[ALERT] OVERLOAD DETECTED on AP1 (Threshold: 50KB breached)`  
> `[ACTION] SDN Controller dynamically Rerouting car2 to AP2...`

**Controller Action Log:**
![Alert Message](screenshots/Στιγμιότυπο%20οθόνης%202026-02-21%20113516.png)

**0% Packet Loss (Terminal Proof):**
![Ping Results](screenshots/Στιγμιότυπο%20οθόνης%202026-02-21%20114027.png)

## How to Run

1. Ensure you have Ubuntu/Linux with **Mininet-WiFi** and **Ryu** installed.
2. Clone this repository:
   ```bash
   git clone https://github.com/andreasf2/SDN-Load-Balancing-VANETs-on-Mininet-Wifi.git
