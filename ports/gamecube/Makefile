# Genuine PowerPC GameCube .dol; no Linux/Node/Wii-specific IOS APIs.
.SUFFIXES:
ifeq ($(strip $(DEVKITPPC)),)
$(error DEVKITPPC required)
endif
include $(DEVKITPPC)/gamecube_rules
TARGET := boot
BUILD := build
SOURCES := source
INCLUDES := ../common
CFLAGS := -O2 -g -Wall -Wextra -ffunction-sections -fdata-sections $(MACHDEP) $(INCLUDE)
LDFLAGS := -g $(MACHDEP) -Wl,-Map,$(notdir $@).map -Wl,--gc-sections
LIBS := -lfat -logc -lm
LIBDIRS :=
ifneq ($(BUILD),$(notdir $(CURDIR)))
export OUTPUT := $(CURDIR)/$(TARGET)
export VPATH := $(CURDIR)/source
export DEPSDIR := $(CURDIR)/$(BUILD)
export LD := $(CC)
export OFILES := main.o
export INCLUDE := -I$(CURDIR)/../common -I$(CURDIR)/$(BUILD) -I$(LIBOGC_INC)
export LIBPATHS := -L$(LIBOGC_LIB)
.PHONY: all clean
all: $(BUILD)
$(BUILD):
	@mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile
clean:
	rm -rf $(BUILD) boot.elf boot.dol boot.elf.map
else
DEPENDS := $(OFILES:.o=.d)
$(OUTPUT).dol: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)
-include $(DEPENDS)
endif
