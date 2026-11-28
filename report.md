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
| luxor | `luxor-macos-26-small` | 27.0 (26.0 to 28.0) | **4.4 (4.1 to 4.9)** | – | – | 30,159 (29,991 to 33,844) | 13,604 (12,777 to 17,125) | 12,016 (11,314 to 14,807) | **98,925 (96,483 to 132,613)** | 60,447 (59,651 to 77,761) | 175 (120 to 230) | **3.9 (3.9 to 4.2)** | **6.7 (5.7 to 7.3)** | **19.9 (18.3 to 20.2)** | $0.0267 ($0.0253 to $0.0280) |
| luxor | `luxor-ubuntu-medium-4c-8g` | **8.0** | 5.1 (5.0 to 5.3) | 6,895 (6,880 to 6,898) | 26,697 (26,539 to 26,785) | **42,336 (42,278 to 42,434)** | **21,080 (20,559 to 22,466)** | **17,465 (14,088 to 18,967)** | 98,024 (96,972 to 114,733) | **111,120 (110,246 to 121,114)** | **217 (145 to 419)** | 4.1 (3.9 to 4.7) | 8.0 (5.6 to 9.1) | 23.6 (23.6 to 23.7) | **$0.0032** |
