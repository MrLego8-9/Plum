package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"plum/io"
	"plum/style"
	"plum/update"
	"sync"
	"syscall"
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
	rebuildVeraFlag := flag.Bool("rebuild-vera", false, "Rebuild vera++")
	ignoreProcessingFlag := flag.Bool("no-ignore", false, "Do not ignore files in .gitignore and .plumignore")
	noStatusFlag := flag.Bool("no-status", false, "Always return with exit code 0")
	versionFlag := flag.Bool("version", false, "Show version")
	flag.Parse()

	if *versionFlag {
		fmt.Print(update.PlumVersion)
		os.Exit(0)
	}

	if *updateFlag {
		if !update.CheckIsUpdateAvailable() {
			fmt.Println("Plum is up to date")
			os.Exit(0)
		}
		fmt.Println("Updating Plum")
		update.PlumUpdate()
		os.Exit(0)
	}

	if *rebuildVeraFlag {
		update.RebuildVera()
	}

	if *updateRulesFlag {
		if os.Getuid() != 0 { // Execve sudo with plum command
			fmt.Println("Plum need elevated privileges to update rules, restarting using sudo")
			execveErr := syscall.Exec("/bin/sudo", append([]string{"/bin/sudo"}, os.Args...), os.Environ())
			if execveErr != nil {
				log.Fatal("execve sudo", execveErr)
			}
		}
		update.PlumUpdateRules()
	}

	if *rebuildVeraFlag || *updateRulesFlag { // Exit after rebuild / update task
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
