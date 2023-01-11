import os
import glob as gl

class PackHandler:

    def gt_pack_data(self, pack, direc):
        return dict(eval(self.gt_pack_str(pack, direc)))

    def gt_pack_str(self, pack, direc):
        try:
            with open(f"{direc}/{pack}.txt", "r", encoding ="utf-8") as file:
                return file.read()
        except:
            raise FileNotFoundError(f"Couldn't fetch pack '{pack}' from directory '{direc}'.")

class LangHandler:

    def __init__(self, cur_lang = "en_US"):
        self.cur_lang = cur_lang
        self.cur_lang_data = ph.gt_pack_data(self.cur_lang, "language packs")

    def get_langs(self):
        lang_paths = gl.glob("language packs/*.txt")
        langs = []
        for lang_path in lang_paths:
            langs.append(os.path.basename(lang_path).split(".txt")[0])
        return langs

    def get_lang_name(self, lang):
        lang_data = ph.gt_pack_data(lang, "language packs")
        try:
            lang_name = lang_data["info"]["name"]
        except:
            raise FileNotFoundError(f"Couldn't fetch info data for 'name' from language pack '{lang}'.")
        return lang_name

    def demo(self):
        try:
            demo = self.cur_lang_data["demo"]
        except:
            raise FileNotFoundError(f"Couldn't fetch demo data from language pack '{self.cur_lang}'.")
        return demo

    def opt_win(self, key):
        try:
            ele = self.cur_lang_data["opt_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'options' window data for '{key}' from language pack '{self.cur_lang}'.")
        return ele

    def abt_win(self, key):
        try:
            ele = self.cur_lang_data["abt_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'about' window data for '{key}' from language pack '{self.cur_lang}'.")
        return ele

    def shc_win(self, key):
        try:
            ele = self.cur_lang_data["shc_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'shortcuts' window data for '{key}' from language pack '{self.cur_lang}'.")
        return ele

    def ver_win(self, key, **kwargs):
        try:
            ele = self.cur_lang_data["ver_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'version_error' window data for '{key}' from language pack '{self.cur_lang}'.")
        if key == "text":
            text = ""
            blocks = ele.split("}")
            if len(blocks) == 1:
                text = blocks[0]
            else:
                for i in range(len(blocks) - 1):
                    txt_arg_pair = blocks[i].split("{", maxsplit=1)
                    if len(txt_arg_pair) == 1:
                        raise SyntaxError(f"Unmatched curly bracket in 'version_error' window data for 'text'.")
                    else:
                        arg = None
                        for kw in kwargs:  # search for matching argument
                            if kw == txt_arg_pair[1]:
                                arg = kwargs[kw]
                        if arg == None:
                            raise TypeError(f"LangHandler.ver_win() missing required keyword argument '{txt_arg_pair[1]}' in 'version_error' window data for '{key}' from language pack '{self.cur_lang}'.")
                        text += txt_arg_pair[0] + str(arg[0]) + "." + str(arg[1])
                text += blocks[len(blocks) - 1]
            return text
        return ele

    def gui(self, key):
        try:
            ele = self.cur_lang_data["gui"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch gui data for '{key}' from language pack '{self.cur_lang}'.")
        return ele

    def file_mng(self, key):
        try:
            ele = self.cur_lang_data["file_mng"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch file_mng data for '{key}' from language pack '{self.cur_lang}'.")
        return ele

    def asm_win(self, key):
        try:
            ele = self.cur_lang_data["asm_win"][key]
        except:
            raise FileNotFoundError(f"Couldn't fetch 'Assembly' window data for '{key}' from language pack '{self.cur_lang}'.")
        if key == "text":
            text_code_pairs = []
            blocks = ele.split("}")
            if len(blocks) == 1:
                text_code_pairs = [(blocks[0], "")]
            else:
                for i in range(len(blocks) - 1):
                    text_code_pair = blocks[i].split("{", maxsplit = 1)
                    if len(text_code_pair) == 1:
                        raise SyntaxError(f"Unmatched curly bracket in 'Assembly' window data for 'text' from language pack '{self.cur_lang}'.")
                    else:
                        text_code_pairs.append(text_code_pair)
                text_code_pairs.append((blocks[len(blocks) - 1], ""))
            return text_code_pairs
        return ele

class ErrorHandler():

    def __init__(self):
        self.errors = ph.gt_pack_data("errors", "resources")

    def error(self, err, **kwargs):
        try:
            err_tpl = self.errors[err]
        except:
            raise FileNotFoundError(f"Couldn't fetch error data for '{err}'.")
        err_name = err_tpl[0]
        err_desc = ""
        blocks = err_tpl[1].split("}")
        if len(blocks) == 1:
            err_desc = blocks[0]
        else:
            for i in range(len(blocks) - 1):
                txt_arg_pair = blocks[i].split("{", maxsplit = 1)
                if len(txt_arg_pair) == 1:
                    raise SyntaxError(f"Unmatched curly bracket in error data for '{err}'.")
                else:
                    arg = None
                    for kw in kwargs: # search for matching argument
                        if kw == txt_arg_pair[1]:
                            arg = kwargs[kw]
                    if arg == None:
                        raise TypeError(f"LangHandler.error() missing required keyword argument '{txt_arg_pair[1]}' in error data for '{err}'.")
                    err_desc += txt_arg_pair[0] + str(arg)
            err_desc += blocks[len(blocks) - 1]
        return err_name + ": " + err_desc

ph = PackHandler()