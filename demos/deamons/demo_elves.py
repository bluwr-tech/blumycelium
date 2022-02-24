import machine_elf as melf

class PrinterElf(melf.MachineElf):
    """An elf that prints somthing on the screen"""
    def task_print_it(self, to_print, suffix=None) -> None:
        if suffix is None:
            suffix = ""

        print(">>> Machine >>> Elf >>> Printer: '%s', suffix: '%s'" % (to_print, suffix))

class SenderElf(melf.MachineElf):
    """An elf that saves a value in database for testing parameters to results passing"""
    def task_send(self, to_send) -> ("value", ):
        return {
            "value": to_send
        }

class KillerElf(melf.MachineElf):
    """An elf that raises an exception"""
    def task_send(self, *args, **kwargs) -> None:
        raise Exception("Hahaha!")
