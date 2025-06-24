package main

import (
	"log"

	"github.com/ktny/ccmonitor/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		log.Fatal(err)
	}
}