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
| luxor | `luxor-macos-26-small` | 26.0 (17.0 to 28.0) | **4.4 (4.3 to 5.3)** | – | – | 30,251 (29,986 to 32,739) | 3,079 (2,764 to 4,991) | 3,891 (1,942 to 6,184) | 15,614 (15,292 to 15,961) | 6,502 (6,452 to 6,952) | **278 (175 to 310)** | 6.6 (6.0 to 8.9) | 17.4 (12.3 to 17.5) | **19.9 (18.5 to 20.4)** | $0.0267 ($0.0253 to $0.0280) |
| luxor | `luxor-ubuntu-medium-4c-8g` | **8.0** | 14.5 (12.6 to 15.7) | 6,968 (6,928 to 6,971) | 26,839 (26,699 to 27,003) | **42,753 (42,101 to 42,987)** | **17,237 (16,446 to 18,631)** | **13,837 (12,336 to 16,468)** | **97,440 (94,525 to 137,649)** | **123,877 (115,806 to 129,912)** | 249 (211 to 331) | **4.0 (3.9 to 4.0)** | **5.8 (4.9 to 10.7)** | 23.6 (23.5 to 23.7) | **$0.0032** |
