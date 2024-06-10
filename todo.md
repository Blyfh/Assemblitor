# TO-DO

* new option: last dir fixed (choose path) or automatic
* create custom Error classes for ASM errors
* make theme colors not hardcoded (save in file)

# BUGS

* will default to save_as() when using save() after aborting one save_as()
* askyesnocancel buttons don't adjust to language
* errors raised in Editor.py won't be redirected to report_callback_exception (will instead be caught by the try/except
  in Assemblitor.pyw) -> esp bad if it's NOT an internal error (won't get displayed in CDB)
* some error messages don't get checked for xvisibility in out_CDB + after xbar is visible, it won't get removed
    * this is a reproducible example:
      ```asm
      ; A simple countdown program
      00 JMP 02
      01 5
      
      03 SUB #1
      04 JLE 07
      05 STA 01
      06 JMP 03
      07 STP
      ```

# SUGGESTIONS

* display ALU
* break points for debugging
* colorcoding for Assembler
* strg + h

