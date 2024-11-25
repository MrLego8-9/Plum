package style

import (
	"bytes"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
)

func walkDirectories(ignoredDirs, ignoredFiles []string) ([]string, error) {
	includedFiles := make([]string, 0)
	err := filepath.Walk(".", func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		for _, ignoredDir := range ignoredDirs {
			if matched, _ := filepath.Match(ignoredDir, path); matched {
				if info.IsDir() {
					return filepath.SkipDir
				}
				return nil
			}
		}
		if !info.IsDir() {
			for _, ignoredFile := range ignoredFiles {
				if matched, _ := filepath.Match(ignoredFile, path); matched {
					return nil
				}
			}
			includedFiles = append(includedFiles, "./"+path)
		}
		return nil
	})
	return includedFiles, err
}

func getCodeToCommentFile() map[string]string {
	codeToCommentHandle, err := os.Open("/usr/local/lib/vera++/code_to_comment")
	if err != nil {
		log.Fatal(err)
	}
	c2cStat, statErr := codeToCommentHandle.Stat()
	if statErr != nil {
		log.Fatal(statErr)
	}
	readBuffer := make([]byte, c2cStat.Size())
	bytesRead, readErr := codeToCommentHandle.Read(readBuffer)
	if readErr != nil {
		log.Fatal(readErr)
	}
	if int64(bytesRead) != c2cStat.Size() {
		log.Fatalf("Read %d bytes but expected %d", bytesRead, c2cStat.Size())
	}
	_ = codeToCommentHandle.Close()
	codeToCommentString := strings.TrimRight(string(readBuffer), "\n")
	codeToCommentLines := strings.Split(codeToCommentString, "\n")
	codeToComment := make(map[string]string)
	for _, line := range codeToCommentLines {
		lineParts := strings.Split(line, ":")
		if len(lineParts) != 2 {
			log.Fatalf("Invalid line in code_to_comment: %s", line)
		}
		codeToComment[lineParts[0]] = lineParts[1]
	}
	return codeToComment
}

func processFilesChunk(chunk []string) string {
	filesToCheck := strings.Join(chunk, "\n")
	stdinBuffer := bytes.NewBufferString(filesToCheck)
	veraCommand := exec.Command("vera++", "--profile", "epitech", "-d")
	veraCommand.Stderr = os.Stderr
	veraCommand.Stdin = stdinBuffer

	veraResult, veraError := veraCommand.Output()
	if veraError != nil {
		log.Fatal(veraError)
	}
	return string(veraResult)
}

func startChecks(includedFiles []string) (*sync.WaitGroup, []chan string) {
	nbFiles := len(includedFiles)
	numCPUCores := max(1, min(nbFiles/5, runtime.NumCPU()-1))
	chunkSize := max(1, nbFiles/numCPUCores)

	waitGroup := sync.WaitGroup{}
	resultsChannels := make([]chan string, 0)
	for i := 0; i < len(includedFiles); i += chunkSize {
		end := i + chunkSize
		if end > nbFiles {
			end = nbFiles
		}

		waitGroup.Add(1)
		channel := make(chan string)
		resultsChannels = append(resultsChannels, channel)
		go func(chunk []string) {
			veraResult := processFilesChunk(chunk)
			waitGroup.Done()
			channel <- veraResult
			close(channel)
		}(includedFiles[i:end])
	}
	return &waitGroup, resultsChannels
}

func processVeraErrors(veraResults []string) (map[string]int, [][]string) {
	codeToComment := getCodeToCommentFile()
	errorCount := map[string]int{"INFO": 0, "MINOR": 0, "MAJOR": 0, "FATAL": 0}
	splitErrors := make([][]string, 0)
	for _, veraError := range veraResults {
		splitError := strings.Split(veraError, ":")
		splitLen := len(splitError)
		if splitLen > 1 {
			level := strings.Trim(splitError[splitLen-2], " ")
			if _, ok := errorCount[level]; ok {
				errorCount[level]++
			}
			splitError[splitLen-2] = level
		}
		if splitLen > 0 {
			errorCode := splitError[splitLen-1]
			if codeMeaning, ok := codeToComment[errorCode]; ok {
				splitError = append(splitError, codeMeaning)
			}
		}
		splitErrors = append(splitErrors, splitError)
	}
	return errorCount, splitErrors
}

func CheckCStyle(ignoredDirs, ignoredFiles []string) (map[string]int, [][]string) {
	ignoredDirs = append([]string{"tests", "bonus", ".git"}, ignoredDirs...)
	includedFiles, err := walkDirectories(ignoredDirs, ignoredFiles)
	if err != nil {
		log.Println("Failed to walk dirs for C Coding Style: ", err)
		return nil, nil
	}
	waitGroup, resultsChannels := startChecks(includedFiles)
	waitGroup.Wait()
	veraResults := make([]string, 0)
	for _, resultChannel := range resultsChannels {
		select {
		case res := <-resultChannel:
			if res != "" {
				resultLine := strings.TrimRight(res, "\n")
				resultLines := strings.Split(resultLine, "\n")
				veraResults = append(veraResults, resultLines...)
			}
		}
	}
	return processVeraErrors(veraResults)
}
