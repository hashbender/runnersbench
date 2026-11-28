package main

import (
	"crypto/rand"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}

func main() {
	dir := os.Args[1]
	const blocks, blockSize = 32, 32 << 20
	buf := make([]byte, blockSize)
	var keys []string
	for i := range blocks {
		_, _ = rand.Read(buf)
		p := filepath.Join(dir, fmt.Sprintf("block-%02d", i))
		must(os.WriteFile(p, buf, 0o600))
		keys = append(keys, p)
	}
	run := func(name string, fn func(dst *os.File)) {
		dst, err := os.Create(filepath.Join(dir, "merged-"+name))
		must(err)
		start := time.Now()
		fn(dst)
		must(dst.Sync())
		must(dst.Close())
		fmt.Printf("%s %.3fs\n", name, time.Since(start).Seconds())
		must(os.Remove(dst.Name()))
	}
	pipe := func(dst *os.File) {
		pr, pw := io.Pipe()
		go func() {
			for _, k := range keys {
				f, err := os.Open(k)
				must(err)
				_, err = io.Copy(pw, f)
				must(err)
				f.Close()
			}
			pw.Close()
		}()
		_, err := io.Copy(dst, pr)
		must(err)
	}
	concat := func(dst *os.File) {
		for _, k := range keys {
			f, err := os.Open(k)
			must(err)
			_, err = io.Copy(dst, f)
			must(err)
			f.Close()
		}
	}
	for range 3 {
		run("pipe", pipe)
		run("concat", concat)
	}
}
