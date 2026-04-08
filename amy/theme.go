package main

import (
	"github.com/gdamore/tcell/v2"
)

type Theme struct {
	Background tcell.Color
	Foreground tcell.Color
	Accent     tcell.Color
	StatusBg   tcell.Color
	StatusFg   tcell.Color
}

var LesbianTheme = Theme{
	Background: tcell.ColorOrangeRed,
	Foreground: tcell.ColorWhite,
	Accent:     tcell.ColorHotPink,
	StatusBg:   tcell.ColorDarkOrange,
	StatusFg:   tcell.ColorWhite,
}
