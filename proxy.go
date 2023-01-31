package main

import (
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	wav "proxy/audiowav"
	"strconv"

	"golang.org/x/net/websocket"
)

func randomPath(suffix string) (string, string) {
	randId := rand.Int63()
	var tag string
	tag = fmt.Sprintf("%x", randId)
	return tag, fmt.Sprintf("./tmp/%x%s", rand.Int63(), suffix)
}

func handleAudio(ws *websocket.Conn) {
	log.Println("handleAudio")
	defer ws.Close()
	sampleFreqString := ws.Request().URL.Query().Get("hz")
	var sampleFreq uint32
	if sampleFreqString == "" {
		sampleFreq = 44100
	} else {
		// parse the sample frequency from the query string into an unsigned 32-bit integer:
		var convErr error
		sampleFreqLong, convErr := strconv.ParseUint(sampleFreqString, 10, 32)
		sampleFreq = uint32(sampleFreqLong)
		if convErr != nil {
			log.Println("error converting sample frequency:", convErr)
			return
		}
	}

	recording := make([]int16, 0)
	idStr, savePath := randomPath(".wav")
	// Create the file at savePath:
	wavFile, err := os.Create(savePath)
	if err != nil {
		log.Println("error creating file:", err)
		return
	}
	defer wavFile.Close()
	streamer, err := wav.StreaminglyWritable(wavFile, sampleFreq)
	if err != nil {
		log.Println("error creating streamer:", err)
		return
	}
	websocket.Message.Send(ws, idStr)
	for {
		var msg []byte
		errWs := websocket.Message.Receive(ws, &msg)

		// if the error is EOF, the client has closed the connection:
		if errWs == io.EOF {
			// flush pending writes:
			if len(msg) > 0 {
				err = streamer(msg)
				if err != nil {
					log.Println("error writing to streamer:", err)
					break
				}
			}
			break
		}

		// otherwise, handle the error:
		if errWs != nil {
			log.Println("error receiving message:", errWs)
			break
		}

		// With no error, append the message to the recording:
		errRecord := streamer(msg)
		if errRecord != nil {
			log.Println("error writing to streamer:", errRecord)
			break
		}
		fmt.Printf("received message: %x\n", msg)
		//err = websocket.Message.Send(ws, "ok")
		//if err != nil {
		//log.Println("error sending message:", err)
		//break
		//}
	}
	fmt.Printf("recording: %x\n", recording)
	log.Println("handleAudio done")
}

func serveAudio(w http.ResponseWriter, r *http.Request) {
	log.Println("serveAudio")
	for _, c := range r.Cookies() {
		fmt.Println("Have cookie: ", c)
	}
	websocket.Handler(handleAudio).ServeHTTP(w, r)
	defer log.Println("serveAudio done")
}

func main() {
	mux := http.NewServeMux()

	proxy := httputil.NewSingleHostReverseProxy(&url.URL{
		Scheme: "http",
		Host:   "127.0.0.1:5001",
	})

	// TODO: serve file individually, delete on completion
	mux.Handle("/browser/", http.StripPrefix("/browser/", http.FileServer(http.Dir("./browser"))))
	mux.Handle("/audio", http.HandlerFunc(serveAudio))
	//mux.Handle("/audio", websocket.Handler(handleAudio))
	mux.Handle("/", proxy)
	//log.Fatal(http.ListenAndServeTLS(":8999", "server.crt", "server.key", mux))
	log.Fatal(http.ListenAndServe(":8999", mux))
	//log.Fatal(http.ListenAndServeTLS("", "", ":8999", mux))
}
