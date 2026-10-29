# STATIC GENESIS Wii / actual Nintendo Wii homebrew output (PowerPC .dol)
# Uses official devkitPro libogc Wii build conventions. No Linux or Node on Wii.
.SUFFIXES:
ifeq ($(strip $(DEVKITPPC)),)
$(error "DEVKITPPC not set; use devkitpro/devkitppc official SDK image")
endif
include $(DEVKITPPC)/wii_rules

TARGET := boot
BUILD := build
SOURCES := source
INCLUDES :=
CFLAGS := -O2 -g -Wall -Wextra -Werror -ffunction-sections -fdata-sections $(MACHDEP) $(INCLUDE)
LDFLAGS := -g $(MACHDEP) -Wl,-Map,$(notdir $@).map -Wl,--gc-sections
LIBS := -lwiiuse -lbte -lfat -logc -lm
LIBDIRS :=

ifneq ($(BUILD),$(notdir $(CURDIR)))
export OUTPUT := $(CURDIR)/$(TARGET)
export VPATH := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR := $(CURDIR)/$(BUILD)
export LD := $(CC)
export OFILES := main.o
export INCLUDE := -I$(CURDIR)/$(BUILD) -I$(LIBOGC_INC)
export LIBPATHS := -L$(LIBOGC_LIB)
.PHONY: all clean
all: $(BUILD)
$(BUILD):
	@mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile
clean:
	rm -rf $(BUILD) $(OUTPUT).elf $(OUTPUT).dol $(OUTPUT).elf.map
else
DEPENDS := $(OFILES:.o=.d)
$(OUTPUT).dol: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)
-include $(DEPENDS)
endif
