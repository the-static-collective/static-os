# Native Nintendo DS ARM9/ARM7 .nds, libnds+Calico; not an Android app.
.SUFFIXES:
ifeq ($(strip $(DEVKITARM)),)
$(error DEVKITARM required for Nintendo DS)
endif
include $(DEVKITARM)/ds_rules
TARGET := genesis
BUILD := build
SOURCES := source
ARCH := -march=armv5te -mtune=arm946e-s -mthumb
CFLAGS := -g -O2 -Wall -Wextra -ffunction-sections -fdata-sections $(ARCH) $(INCLUDE) -DARM9
LDFLAGS := -specs=ds_arm9.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)
LIBS := -lfat -lnds9
LIBDIRS := $(LIBNDS)
GAME_TITLE := STATIC GENESIS
GAME_SUBTITLE1 := What shall we build?
GAME_SUBTITLE2 := Offline first-boot proposal
ifneq ($(BUILD),$(notdir $(CURDIR)))
export OUTPUT := $(CURDIR)/$(TARGET)
export VPATH := $(CURDIR)/source
export DEPSDIR := $(CURDIR)/$(BUILD)
export LD := $(CC)
export OFILES := main.o
export INCLUDE := -I$(CURDIR)/../common -I$(CURDIR)/$(BUILD) -I$(LIBNDS)/include
export LIBPATHS := -L$(LIBNDS)/lib -L$(DEVKITPRO)/libfat/lib
.PHONY: all clean
all: $(BUILD)
$(BUILD):
	@mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile
clean:
	rm -rf $(BUILD) genesis.nds genesis.elf genesis.elf.map
else
DEPENDS := $(OFILES:.o=.d)
$(OUTPUT).nds: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)
-include $(DEPENDS)
endif
