package main

import (
	"flag"
	"log"
	"os"
	"os/exec"
	"plum/io"
	"plum/style"
	"sync"
)

func runChecks(ignoredDirs, ignoredFiles []string) (io.CheckResult, io.CheckResult) {
	cChannel := make(chan io.CheckResult)
	haskellChannel := make(chan io.CheckResult)
	waitGroup := sync.WaitGroup{}
	waitGroup.Add(2)
	go func() { // Run C checks
		errorCount, errors := style.CheckCStyle(ignoredDirs, ignoredFiles)
		waitGroup.Done()
		cChannel <- io.CheckResult{ErrorCount: errorCount, Errors: errors}
		close(cChannel)
	}()
	go func() { // Run Haskell checks
		errorCount, errors := style.CheckHaskellStyle(ignoredDirs, ignoredFiles)
		waitGroup.Done()
		haskellChannel <- io.CheckResult{ErrorCount: errorCount, Errors: errors}
		close(haskellChannel)
	}()
	waitGroup.Wait()
	var cResult io.CheckResult
	var haskellResult io.CheckResult
	select {
	case cRes := <-cChannel:
		cResult = cRes
	}
	select {
	case haskellRes := <-haskellChannel:
		haskellResult = haskellRes
	}
	return cResult, haskellResult
}

func main() {
	updateFlag := flag.Bool("update", false, "Update Plum")
	updateRulesFlag := flag.Bool("update-rules", false, "Update the coding style rules")
	ignoreProcessingFlag := flag.Bool("no-ignore", false, "Do not ignore files in .gitignore and .plumignore")
	noStatusFlag := flag.Bool("no-status", false, "Always return with exit code 0")
	flag.Parse()

	if *updateFlag {
		err := exec.Command("/opt/plum-coding-style/plum_update.sh").Run()
		if err != nil {
			log.Fatal(err)
		}
		os.Exit(0)
	}

	if *updateRulesFlag {
		err := exec.Command("/opt/plum-coding-style/plum_update.sh", "--update-rules").Run()
		if err != nil {
			log.Fatal(err)
		}
		os.Exit(0)
	}

	ignoredDirs, ignoredFiles, err := io.GetIgnoredFiles(*ignoreProcessingFlag)
	if err != nil {
		log.Fatal(err)
	}

	cErrors, haskellErrors := runChecks(ignoredDirs, ignoredFiles)
	hasErrors := io.PrintErrors(cErrors, haskellErrors)
	if *noStatusFlag || !hasErrors {
		os.Exit(0)
	}
	os.Exit(1)
}
