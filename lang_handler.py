class LangHandler:

    def __init__(self, cur_lang = "en_US"):
        self.cur_lang = cur_lang
        self.cur_lang_data = self.gt_lang_data(self.cur_lang)

    def gt_lang_data(self, lang):
        return dict(eval(self.gt_lang_str(lang)))

    def gt_lang_str(self, lang):
        try:
            with open("language_packs/" + lang + ".txt", "r") as file:
                return file.read()
        except:
            raise FileNotFoundError("Couldn't fetch language pack '" + lang + "'.")

    def demo(self):
        try:
            demo = self.cur_lang_data["demo"]
        except:
            raise FileNotFoundError("Couldn't fetch demo data from language pack '" + self.cur_lang + "'.")
        return demo

    def error(self, err, **kwargs):
        try:
            err_tpl = self.cur_lang_data["error"][err]
        except:
            raise FileNotFoundError("Couldn't fetch error data for '" + err + "' from language pack '" + self.cur_lang + "'.")
        err_name = err_tpl[0]
        err_desc = ""
        blocks = err_tpl[1].split("}")
        if len(blocks) == 1:
            err_desc = blocks[0]
        else:
            for i in range(len(blocks) - 1):
                txt_arg_pair = blocks[i].split("{", maxsplit = 1)
                if len(txt_arg_pair) == 1:
                    raise SyntaxError("Unmatched '}' in error data for '" + err + "' from language pack '" + self.cur_lang + "'.")
                else:
                    arg = None
                    for kw in kwargs: # search for matching argument
                        if kw == txt_arg_pair[1]:
                            arg = kwargs[kw]
                    if arg == None:
                        raise TypeError("LangHandler.error() missing required keyword argument '" + txt_arg_pair[1] + "' in error data for '" + err + "' from language pack '" + self.cur_lang + "'.")
                    err_desc += txt_arg_pair[0] + str(arg)
            err_desc += blocks[len(blocks) - 1]
        if err == "PythonVer":
            return err_name, err_desc
        else:
            return err_name + ": " + err_desc