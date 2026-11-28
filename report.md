# Runner benchmark report

Benchmark version 5. 6 samples from 1 workflow run(s). Benchmark values are medians across samples, with the lowest to highest sample in brackets; the best median in each column is bold.

## Runners

| Provider | Label | CPU | vCPUs | Memory (GiB) | Disk (GB) | Virtualization | Location | Network | Samples |
|---|---|---|---|---|---|---|---|---|---|
| luxor | `luxor-macos-26-small` | Apple M4 Pro (Virtual) | 4 | 8.0 | 449 | apple | Seattle, US | AS19538 Luxor | 3 |
| luxor | `luxor-ubuntu-medium-4c-8g` | AMD Ryzen 9 9950X 16-Core Processor | 4 | 7.8 | 156 | kvm | Seattle, US | AS19538 Luxor | 3 |

## Benchmarks

| Provider | Label | Queue (s) | Package install (s) | CPU 1 thread (events/s) | CPU all threads (events/s) | Memory (MiB/s) | Seq read (MB/s) | Seq write (MB/s) | 4k rand read (IOPS) | 4k rand write (IOPS) | fsync writes (/s) | Download (MB/s) | Cache save 1 GB (s) | Cache restore 1 GB (s) | Docker build, no cache (s) | Docker build, cached (s) | Redis build (s) | $ per Redis build |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luxor | `luxor-macos-26-small` | 26.0 (26.0 to 27.0) | 5.4 (4.6 to 5.4) | – | – | 30,494 (30,407 to 33,830) | 13,659 (12,779 to 17,061) | 12,029 (11,204 to 14,690) | **98,304 (96,639 to 132,945)** | 58,845 (57,825 to 76,436) | – | 465 (365 to 563) | **4.0 (3.9 to 4.2)** | 2.8 (2.8 to 2.9) | – | – | **19.9 (18.1 to 20.1)** | $0.0267 ($0.0253 to $0.0280) |
| luxor | `luxor-ubuntu-medium-4c-8g` | **6.0 (6.0 to 7.0)** | **5.1 (5.0 to 5.1)** | 6,899 (6,878 to 6,904) | 26,804 (26,799 to 26,833) | **42,504 (42,490 to 42,630)** | **19,136 (17,965 to 23,886)** | **15,392 (15,101 to 19,853)** | 96,020 (80,280 to 99,682) | **111,380 (105,475 to 115,941)** | 25,881 (23,273 to 26,513) | **502 (129 to 529)** | 4.2 (4.0 to 4.2) | **1.6 (1.4 to 1.6)** | 11.5 (11.3 to 13.3) | 4.9 | 23.6 (23.5 to 23.6) | **$0.0032** |

## Errors

- `luxor-ubuntu-medium-4c-8g` docker: the cached build didn't reuse the npm ci layer
- `luxor-ubuntu-medium-4c-8g` docker: the cached build didn't reuse the npm ci layer
