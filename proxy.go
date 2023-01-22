package main

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"log"
)

func main() {
	mux := http.NewServeMux()

	proxy := httputil.NewSingleHostReverseProxy(&url.URL{
		Scheme: "http",
		Host:   "127.0.0.1:5001",
	})

	// TODO: serve file individually, delete on completion
	mux.Handle("/browser/", http.StripPrefix("/browser/", http.FileServer(http.Dir("./browser"))))
	mux.Handle("/", proxy)
	log.Fatal(http.ListenAndServe(":8999", mux))
}
