package update

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strings"
)

const PlumVersion = "3.1.1"

const remotePlumBinary = "/tmp/plum"

func downloadPlumBinary(outputPath string) error {
	wgetOutput, wgetErr := exec.Command("wget", "-O", outputPath, "https://github.com/MrLego8-9/Plum/releases/latest/download/plum").CombinedOutput()
	if wgetErr != nil {
		_, _ = fmt.Fprintln(os.Stderr, "wget ", wgetErr)
		_, _ = fmt.Fprintln(os.Stderr, string(wgetOutput))
		return wgetErr
	}
	chmodErr := os.Chmod(outputPath, 0755)
	if chmodErr != nil {
		_, _ = fmt.Fprintln(os.Stderr, "chmod ", chmodErr)
		return chmodErr
	}
	return nil
}

func CheckIsUpdateAvailable() bool {
	wgetErr := downloadPlumBinary(remotePlumBinary)
	if wgetErr != nil {
		return false
	}
	remotePlumVersionBytes, remotePlumVersionErr := exec.Command(remotePlumBinary, "--version").Output()
	if remotePlumVersionErr != nil {
		_, _ = fmt.Fprintln(os.Stderr, "get remote version ", remotePlumVersionErr)
		return false
	}
	remotePlumVersion := strings.TrimSpace(string(remotePlumVersionBytes))
	removeErr := os.Remove(remotePlumBinary)
	if removeErr != nil {
		_, _ = fmt.Fprintln(os.Stderr, "remove plum ", removeErr)
	}
	if remotePlumVersion > PlumVersion {
		return true
	}
	return false
}

func PlumUpdate() {
	installScriptResponse, getErr := http.Get("https://raw.githubusercontent.com/MrLego8-9/Plum/main/plum_install.sh")
	if getErr != nil {
		log.Fatal("Failed to get install script ", getErr)
	}
	if installScriptResponse.StatusCode != 200 {
		log.Fatal("Failed get install script, expected 200 but got ", installScriptResponse.Status)
	}
	installScript, responseErr := io.ReadAll(installScriptResponse.Body)
	if responseErr != nil {
		log.Fatal("Failed to read install script ", responseErr)
	}
	closeErr := installScriptResponse.Body.Close()
	if closeErr != nil {
		log.Fatal("Failed to close install script ", closeErr)
	}
	bashExecCommand := exec.Command("bash")
	bashExecCommand.Stderr = os.Stderr
	bashExecCommand.Stdout = os.Stdout
	stdinBuffer := bytes.NewBuffer(installScript)
	bashExecCommand.Stdin = stdinBuffer
	bashErr := bashExecCommand.Run()
	if bashErr != nil {
		log.Fatal("Failed to execute install script ", bashErr)
	}
}
