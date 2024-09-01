package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"sort"
	"strings"
)

type Graph struct {
	nodes map[string]struct{}
	edges map[[2]string]struct{}
}

func main() {
	if len(os.Args) != 3 {
		log.Fatalf("Usage: %s <old-graph-file> <new-graph-file>", os.Args[0])
	}

	oldGraph, err := readGraph(os.Args[1])
	if err != nil {
		log.Fatalf("Failed to read %s: %s", os.Args[1], err)
	}

	newGraph, err := readGraph(os.Args[2])
	if err != nil {
		log.Fatalf("Failed to read %s: %s", os.Args[2], err)
	}

	printGraphDiff(oldGraph, newGraph)
}

func readGraph(filename string) (Graph, error) {
	graph := Graph{
		nodes: make(map[string]struct{}),
		edges: make(map[[2]string]struct{}),
	}

	file, err := os.Open(filename)
	if err != nil {
		return graph, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var latestNode string
	for scanner.Scan() {
		line := scanner.Text()
		dash := strings.Index(line, " - ")
		if dash == -1 {
			// Ignore invalid lines
			continue
		}

		name := line[:dash]
		if strings.HasPrefix(name, "  ") {
			// It's an edge
			name = strings.TrimSpace(name)
			edge := [2]string{latestNode, name}
			if _, exists := graph.nodes[name]; !exists {
				log.Printf("Warning: Edge reference to undefined node %s", name)
				continue
			}
			graph.edges[edge] = struct{}{}
		} else {
			// It's a node
			latestNode = name
			graph.nodes[name] = struct{}{}
		}
	}

	if err := scanner.Err(); err != nil {
		return graph, err
	}

	return graph, nil
}

func printGraphDiff(old, new Graph) {
	var nodes []string
	nodeSet := make(map[string]struct{})

	// Collect all nodes from both graphs
	for n := range old.nodes {
		nodeSet[n] = struct{}{}
	}
	for n := range new.nodes {
		nodeSet[n] = struct{}{}
	}

	for n := range nodeSet {
		nodes = append(nodes, n)
	}
	sort.Strings(nodes)

	var edges [][2]string
	edgeSet := make(map[[2]string]struct{})

	// Collect all edges from both graphs
	for e := range old.edges {
		edgeSet[e] = struct{}{}
	}
	for e := range new.edges {
		edgeSet[e] = struct{}{}
	}

	for e := range edgeSet {
		edges = append(edges, e)
	}
	sort.Slice(edges, func(i, j int) bool {
		if edges[i][0] != edges[j][0] {
			return edges[i][0] < edges[j][0]
		}
		return edges[i][1] < edges[j][1]
	})

	fmt.Println("digraph G {")
	fmt.Println("  rankdir = \"BT\";")
	fmt.Println()

	// Print nodes with their attributes
	for _, n := range nodes {
		var attrs string
		_, inOld := old.nodes[n]
		_, inNew := new.nodes[n]

		switch {
		case inOld && inNew:
			// No attributes needed for nodes present in both graphs
		case inOld:
			attrs = " [color=red]" // Node removed
		case inNew:
			attrs = " [color=green]" // Node added
		}
		fmt.Printf("    %q%s;\n", n, attrs)
	}

	fmt.Println()

	// Print edges with their attributes
	for _, e := range edges {
		var attrs string
		_, inOld := old.edges[e]
		_, inNew := new.edges[e]

		switch {
		case inOld && inNew:
			// No attributes needed for edges present in both graphs
		case inOld:
			attrs = " [color=red]" // Edge removed
		case inNew:
			attrs = " [color=green]" // Edge added
		}
		fmt.Printf("    %q -> %q%s;\n", e[0], e[1], attrs)
	}

	fmt.Println("}")
}
