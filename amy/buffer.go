package main

type Buffer struct {
	Lines []string
}

func NewBuffer() *Buffer {
	return &Buffer{
		Lines: []string{""},
	}
}

func (b *Buffer) InsertChar(y, x int, ch rune) {
	line := b.Lines[y]
	b.Lines[y] = line[:x] + string(ch) + line[x:]
}

func (b *Buffer) InsertNewLine(y, x int) {
	line := b.Lines[y]
	newLine := line[x:]

	b.Lines[y] = line[:x]
	b.Lines = append(b.Lines[:y+1],
	append([]string{newLine}, b.Lines[y+1:]...)...)
}

func (b *Buffer) Backspace(y, x int) (int, int) {
	if x > 0 {
		line := b.Lines[y]
		b.Lines[y] = line[:x-1] + line[x:]
		return y, x - 1
	}

    return y, x
}


