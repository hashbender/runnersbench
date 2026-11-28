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
| luxor | `luxor-macos-26-small` | 30.0 (29.0 to 30.0) | 5.2 (4.6 to 5.2) | – | – | 30,460 (30,426 to 33,792) | 13,431 (12,465 to 16,487) | 12,066 (11,388 to 14,808) | **96,637 (96,033 to 132,440)** | 59,234 (58,551 to 77,364) | 205 (203 to 221) | 4.3 (4.3 to 4.5) | 3.0 (2.8 to 3.2) | **20.0 (18.3 to 20.2)** | $0.0267 ($0.0253 to $0.0280) |
| luxor | `luxor-ubuntu-medium-4c-8g` | **10.0** | **5.0 (5.0 to 5.1)** | 6,906 (6,882 to 6,986) | 26,967 (26,744 to 27,210) | **42,689 (42,381 to 43,474)** | **18,489 (17,165 to 19,263)** | **16,562 (15,263 to 17,910)** | 95,856 (80,432 to 102,341) | **120,859 (117,732 to 135,244)** | **380 (343 to 397)** | **4.2 (4.2 to 4.4)** | **1.5 (1.5 to 1.8)** | 23.6 (23.3 to 23.7) | **$0.0032** |
