package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"plum/io"
	"plum/style"
	"plum/update"
	"strconv"
	"strings"
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

	if *updateRulesFlag {
		if os.Getuid() != 0 {
			fmt.Println("Plum need elevated privileges to update rules, restarting using sudo")
			elevatedCommand := exec.Command("sudo", os.Args[0], "--update-rules")
			elevatedCommand.Stderr = os.Stderr
			elevatedCommand.Stdout = os.Stdout
			elevatedCommand.Stdin = os.Stdin
			elevatedErr := elevatedCommand.Run()
			if elevatedErr != nil {
				errorString := elevatedErr.Error()
				if strings.HasPrefix(errorString, "exit status ") { // Parse the error message to exit with the correct status
					errorString = strings.TrimPrefix(errorString, "exit status ")
					exitStatus, atoiErr := strconv.Atoi(errorString)
					if atoiErr != nil {
						log.Fatal(atoiErr)
					}
					os.Exit(exitStatus)
				}
			}
			os.Exit(0)
		}
		fmt.Println("\nUpdating Rules")
		update.PlumUpdateRules()
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
