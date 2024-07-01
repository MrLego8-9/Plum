package style

import (
	"log"
	"os/exec"
	"strings"
)

func processLambdananasErrors(lambdananasErrors []string) (map[string]int, [][]string) {
	errorCount := map[string]int{"INFO": 0, "MINOR": 0, "MAJOR": 0, "FATAL": 0}
	splitErrors := make([][]string, 0)
	for _, lamdananasError := range lambdananasErrors {
		splitError := strings.Split(lamdananasError, ":")
		splitLen := len(splitError)
		if splitLen != 4 {
			shortLine := strings.Split(lamdananasError, " ")
			splitErrors = append(splitErrors, []string{shortLine[0], lamdananasError})
			continue
		}
		level := strings.Trim(splitError[splitLen-2], " ")
		if _, ok := errorCount[level]; ok {
			errorCount[level]++
		}
		splitError[splitLen-2] = level
		errorMessage := splitError[splitLen-1]
		errorMessageParts := strings.Split(errorMessage, "#")
		for partIdx, part := range errorMessageParts {
			errorMessageParts[partIdx] = strings.TrimSpace(part)
		}
		splitError = append(splitError[:splitLen-1], errorMessageParts...)
		splitErrors = append(splitErrors, splitError)
	}
	return errorCount, splitErrors
}

func CheckHaskellStyle(ignoredDirs, ignoredFiles []string) (map[string]int, [][]string) {
	ignoredContent := append(ignoredDirs, ignoredFiles...)
	trimmedIgnoredContent := make([]string, 0)
	for _, content := range ignoredContent {
		trimmedIgnoredContent = append(trimmedIgnoredContent, strings.TrimPrefix(content, "./"))
	}
	excludedContent := strings.Trim("Setup.hs:setup.hs:.git:.stack-work:test:tests:bonus"+strings.Join(trimmedIgnoredContent, ":"), ":")
	lambdananasResult, lambdaError := exec.Command("lambdananas", "-o", "vera", "--exclude", excludedContent, ".").Output()
	if lambdaError != nil {
		log.Fatal(lambdaError)
	}
	lambdananasResultString := strings.TrimRight(string(lambdananasResult), "\n")
	lambdananasErrors := strings.Split(lambdananasResultString, "\n")

	return processLambdananasErrors(lambdananasErrors)
}
