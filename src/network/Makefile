# ============================================================
#  libyurinet — Makefile
#  Targets Windows 11 via MinGW-w64 (gcc)
#  Cross-compilation friendly: override CC and TARGET_OS
# ============================================================

CC      = gcc
TARGET  = libyurinet.dll
SRCS    = net.c tcp.c sockets.c dns.c

BUILDDIR = build
OBJS     = $(patsubst %.c, $(BUILDDIR)/%.o, $(SRCS))

CFLAGS  = -Wall -Wextra -O2 -std=c11
DEFINES = -DLIBYURI_BUILD_DLL

WIN_LDFLAGS = -shared -lws2_32
LINUX_LDFLAGS = -shared -fPIC

ifeq ($(OS), Windows_NT)
    LDFLAGS = $(WIN_LDFLAGS)
    RM      = del /Q
    MKDIR   = if not exist $(BUILDDIR) mkdir $(BUILDDIR)
else
    LDFLAGS = $(LINUX_LDFLAGS)
    RM      = rm -f
    MKDIR   = mkdir -p $(BUILDDIR)
endif

.PHONY: all clean rebuild

all: $(BUILDDIR) $(TARGET)
	@echo Done! $(TARGET) is ready.

$(BUILDDIR):
	$(MKDIR)

# Link
$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# Compile each .c -> build/.o
$(BUILDDIR)/%.o: %.c
	$(CC) $(CFLAGS) $(DEFINES) -c $< -o $@

clean:
	$(RM) $(BUILDDIR)/*.o $(TARGET)

rebuild: clean all

TEST_SRC = test_net.c
TEST_BIN = test_net.exe

test: all
	$(CC) $(CFLAGS) -o $(TEST_BIN) $(TEST_SRC) -L. -lyurinet -lws2_32
	@echo Run: $(TEST_BIN)
