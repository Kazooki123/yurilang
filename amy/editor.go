package main

import (
	"github.com/gdamore/tcell/v2"
	"os"
)

type Mode int

const (
	NORMAL Mode = iota
	INSERT
)

type Editor struct {
	exit    bool
	screen  tcell.Screen
	buffer  *Buffer
	cursorX int
	cursorY int
	mode    Mode
	theme   Theme
}

func NewEditor() *Editor {
	s, _ := tcell.NewScreen()
	s.Init()

	return &Editor{
		exit:   false,
		screen: s,
		buffer: NewBuffer(),
		mode:   NORMAL,
		theme:  LesbianTheme,
	}
}

func (e *Editor) Run() {
	defer e.screen.Fini()

	for {
		if e.exit {
			break
		}

		e.draw()
		ev := e.screen.PollEvent()

		switch ev := ev.(type) {
		case *tcell.EventKey:
			e.handleKey(ev)
		}
	}
}

func (e *Editor) handleKey(ev *tcell.EventKey) {
	switch e.mode {

	case NORMAL:
		switch ev.Key() {
		case tcell.KeyCtrlQ:
			e.exit = true // TODO: Additional checks before exiting

		case tcell.KeyCtrlS:
			e.save()

		case tcell.KeyRune:
			if ev.Rune() == 'i' {
				e.mode = INSERT
			}
		}

	case INSERT:
		switch ev.Key() {
		case tcell.KeyEsc:
			e.mode = NORMAL

		case tcell.KeyEnter:
			e.insertNewLine()

		case tcell.KeyBackspace, tcell.KeyBackspace2:
			e.backspace()

		case tcell.KeyRune:
			e.insertChar(ev.Rune())
		}
	}
}

func (e *Editor) insertChar(r rune) {
	e.buffer.InsertChar(e.cursorY, e.cursorX, r)
	e.cursorX++
}

func (e *Editor) insertNewLine() {
	e.buffer.InsertNewLine(e.cursorY, e.cursorX)
	e.cursorY++
	e.cursorX = 0

}

func (e *Editor) save() {
	f, _ := os.Create("output.yuri")
	defer f.Close()

	for _, line := range e.buffer.Lines {
		f.WriteString(line + "\n")
	}
}

func (e *Editor) draw() {
	e.screen.Clear()

	style := tcell.StyleDefault.Foreground(e.theme.Foreground)

	for y, line := range e.buffer.Lines {
		for x, ch := range line {
			e.screen.SetContent(x, y, ch, nil, style)
		}
	}

	// Status bar
	_, height := e.screen.Size()
	status := "[Amy λ] MODE: "

	if e.mode == INSERT {
		status += "INSERT"
	} else {
		status += "NORMAL"
	}

	for i, ch := range status {
		e.screen.SetContent(i, height-1, ch, nil,
			tcell.StyleDefault.
				Background(e.theme.StatusBg).
				Foreground(e.theme.StatusFg))
	}

	e.screen.ShowCursor(e.cursorX, e.cursorY)
	e.screen.Show()
}

func (e *Editor) backspace() {
	y, x := e.buffer.Backspace(e.cursorY, e.cursorX)
	e.cursorY = y
	e.cursorX = x
}
