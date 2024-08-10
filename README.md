# Assemblitor

<img src="https://github.com/Blyfh/Assemblitor/blob/main/program/sprites/Assemblitor/icon.png" align="left" width="100"/>

Assemblitor is a light-weight editor for a simple dialect of Assembly.

Easily write, edit and execute your code in a visual user interface that comes with some quick tools to help you
develop.
<br clear="left"/>

# Requirements

* Python 3.10+
* Pillow 10.0.0+

# Getting Started

Open "Assemblitor/Assemblitor.pyw" to start the program.

## The Language

This Assembly dialect is a low-level column-oriented programming language that is close to machine code. It is
case-insensitive.

The language consists of a sequence of memory cells (MCs) that can store values or commands. Each MC starts with its
address and ends with a line break. The MCs have to be in increasing order but empty ones don't have to be displayed. A
value has to be stored after the address as an integer. An empty MC will be interpreted as having a value of 0. A
command is also stored after the address, with most of them requiring operands to work.
Comments can be made with a semicolon. All text between the semicolon and the next line break will be ignored by the
computer.

The program orients itself to the architecture of a von Neumann processor. This means it takes usage of the program
counter (PC), the accumulator (ACC) and the instruction register (IR). The PC is set to 0 by default. If the program is
executed, the command at the address stored in the PC will be loaded into the IR. There the command can be executed.
After its execution the PC gets increased by one (excluding jumps and stops) and the next command can be loaded into the
IR.

A simple program may look like this:

```asm
00 LDA #4 ; load the value 4 into the ACC
01 STA 04 ; store the value of the ACC into the 4th MC
02 STP    ; stop the program
```

This would be the result after executing the program:

```asm
00 LDA #4
01 STA 04
02 STP
04 4      ; a stored value
```

All accepted commands:

| Command   | Description                                                                                                                            |
|:----------|:---------------------------------------------------------------------------------------------------------------------------------------|
| `STP`     | Stops the program                                                                                                                      |
| `LDA n`   | Loads the value at MC n into the ACC                                                                                                   |
| `LDA #n`  | Loads the value n into the ACC                                                                                                         |
| `LDA (n)` | Loads the value of the MC that has the address that is stored in MC n into the ACC                                                     |
| `STA n`   | Stores the value of the ACC into MC n                                                                                                  |
| `ADD n`   | Adds the value at MC n to the value of the ACC and stores the result into the ACC                                                      |
| `ADD #n`  | Adds the value n to the value of the ACC and stores the result into the ACC                                                            |
| `ADD (n)` | Adds the value of the MC that has the address that is stored in MC n to the value of the ACC and stores the result into the ACC        |
| `SUB n`   | Subtracts the value at MC n from the value of the ACC and stores the result into the ACC                                               |
| `SUB #n`  | Subtracts the value n from the value of the ACC and stores the result into the ACC                                                     |
| `SUB (n)` | Subtracts the value of the MC that has the address that is stored in MC n from the value of the ACC and stores the result into the ACC |
| `MUL n`   | Multiplies the value at MC n by the value of the ACC and stores the result into the ACC                                                |
| `MUL #n`  | Multiplies the value n by the value of the ACC and stores the result into the ACC                                                      |
| `MUL (n)` | Multiplies the value of the MC that has the address that is stored in MC n by the value of the ACC and stores the result into the ACC  |
| `JMP n`   | Jumps to MC n by setting the PC to n                                                                                                   |
| `JZE n`   | Jumps to MC n by setting the PC to n if the value of the ACC is equal to zero                                                          |
| `JLE n`   | Jumps to MC n by setting the PC to n if the value of the ACC is less than or equal to zero                                             |

## The Editor

The editor consists of a menubar, a toolbar and the two code blocks. Write your Assembly program in the left code block
and execute it by clicking the green button on the left of the toolbar. You will find your executed code in the right
code block. Use the orange button to execute one step at a time.
If you want to adjust addresses or operands, you can use the de-/increment tool found right to the execution buttons on
the toolbar. Simply select the code you want to change and click the blue buttons. You can adjust the step size through
the spinbox and which numbers it should affect with the option menu.

### Shortcuts

| Shortcut              | Description                |
|:----------------------|:---------------------------|
| `F5`                  | Run program                |
| `Shift + F5`          | Run single step            |
| `Ctrl + Z`            | Undo change                |
| `Ctrl + Shift + Z`    | Redo change                |
| `Ctrl + Y`            | Redo change                |
| `Ctrl + Backspace`    | Delete whole word          |
| `Shift + Enter`       | Line break without address |
| `Shift + Tab`         | Switch affected numbers    |
| `Shift + Scroll up`   | Increment affected numbers |
| `Shift + Scroll down` | Decrement affected numbers |
| `Ctrl + N`            | New file                   |
| `Ctrl + O`            | Open file                  |
| `Ctrl + R`            | Reload file                |
| `Ctrl + S`            | Save file                  |
| `Ctrl + Shift + S`    | Save file as               |

# Known Bugs

*See "todo.md"*

# Acknowledgments

The whole project is rooted in and inspired by an old Delphi emulator used by my school at that time. In fact, the
Assembly dialect is almost exactly the same, with a few added conveniences and a more open spacing/commenting syntax.

# Contributing

Found a bug? Tell me on [GitHub](https://github.com/Blyfh/assemblitor/issues/new). You can also contribute by suggesting
features or translating Assemblitor to another language.
