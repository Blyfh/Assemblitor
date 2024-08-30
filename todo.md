# TO-DO

* new option: last dir fixed (choose path) or automatic
* create custom Error classes for ASM errors
* make theme colors not hardcoded (save in file)

# BUGS

* tkinter.messagebox.askyesnocancel() buttons don't adjust to program language and will instead use the OS language
* errors raised in Editor.py won't be redirected to report_callback_exception (will instead be caught by the try/except
  in Assemblitor.pyw) -> esp bad if it's NOT an internal error (won't get displayed in CDB)
* if x_BAR is directly on the line that is triggering x_BAR.is_needed, it rapidly alternates between turning visible and invisible
    * reproducible example: ````asm
      00 JMP 02
      01 5
      03 SUB #1
      04 JLE 07
      05 STA 01
      06 JMP 03
      07 STP
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ;
      ; A simple countdown programmmmmmm````

# SUGGESTIONS

* display ALU
* break points for debugging
* colorcoding for Assembler
* ctrl + h

