# Runner benchmark report

Benchmark version 3. 6 samples from 1 workflow run(s). Benchmark values are medians across samples, with the lowest to highest sample in brackets; the best median in each column is bold.

## Runners

| Provider | Label | CPU | vCPUs | Memory (GiB) | Disk (GB) | Virtualization | Location | Network | Samples |
|---|---|---|---|---|---|---|---|---|---|
| luxor | `luxor-macos-26-small` | Apple M4 Pro (Virtual) | 4 | 8.0 | 449 | apple | Seattle, US | AS19538 Luxor | 3 |
| luxor | `luxor-ubuntu-medium-4c-8g` | AMD Ryzen 9 9950X 16-Core Processor | 4 | 7.8 | 156 | kvm | Seattle, US | AS19538 Luxor | 3 |

## Benchmarks

| Provider | Label | Queue (s) | Package install (s) | CPU 1 thread (events/s) | CPU all threads (events/s) | Memory (MiB/s) | Seq read (MB/s) | Seq write (MB/s) | 4k rand read (IOPS) | 4k rand write (IOPS) | Download (MB/s) | Cache save 1 GB (s) | Cache restore 1 GB (s) | Redis build (s) | $ per Redis build |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luxor | `luxor-macos-26-small` | 28.0 (27.0 to 28.0) | **4.4 (4.3 to 4.9)** | – | – | 31,689 (31,673 to 33,722) | 12,938 (12,144 to 16,142) | 11,464 (10,869 to 14,143) | 97,685 (96,135 to 132,172) | 59,259 (59,149 to 77,854) | **274 (165 to 294)** | **4.0 (3.8 to 4.2)** | 15.5 (14.7 to 15.7) | **20.0 (18.2 to 20.0)** | $0.0267 ($0.0253 to $0.0280) |
| luxor | `luxor-ubuntu-medium-4c-8g` | **7.0** | 5.1 (5.0 to 5.9) | 6,911 (6,779 to 6,986) | 26,744 (26,063 to 27,245) | **42,865 (41,816 to 43,417)** | **18,655 (14,972 to 24,938)** | **13,878 (13,367 to 16,270)** | **121,726 (102,737 to 134,794)** | **121,966 (120,431 to 158,843)** | 177 (147 to 401) | 4.3 (4.0 to 4.7) | **5.6 (4.6 to 5.9)** | 23.5 (23.3 to 25.2) | **$0.0032 ($0.0032 to $0.0035)** |
