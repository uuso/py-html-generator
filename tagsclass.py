class Tag:
    """
    Класс реализует возможность создавать HTML-тэги в Python. 
    Класс Tag(tag(str), klass(str or tuple or list), is_single(bool), <tag-properties as **kwargs>) --
        позволяет работать с любым тэгом, задавать ему .text, аргументы, вложенные тэги.
    Добавление вложенного тега организовано перегрузкой оператора '+=' (__iadd__).
    Поддерживается работа с контекстным менеджером, приведение экземпляра к str.
    Метод .get_lines(indent, set_offset) вернёт список из строк тега с учётом отступов во вложенных тэгах:
        - аргумент indent(str) отвечает за формат отступов вложенных элементов, 
        - аргумент set_offset(int) даст отступы формата indent(str) самому тэгу -- для случая необходимости вставки его указанное место файла.
    """
    def __init__(self, tag, klass = (), is_single = False, **kwargs):
        self.tag = tag
        self.attributes = {}
        self.is_single = is_single
        self.children = []
        self.text = ""
        self.indent = 4*' ' # Для вывода дочерних элементов по-умолчанию используется четыре пробела

        if klass: # Если что-либо указали в аргументе klass
            if type(klass) is tuple or type(klass) is list: # Опишем, если несколько классов для тега
                self.attributes['class'] = ' '.join(klass)
            elif type(klass) is str: # Опишем, если один лишь класс передан в виде строки
                self.attributes['class'] = klass
        
        # Все аттрибуты вместе с классом тега будут храниться в словаре
        for attr, value in kwargs.items():             
            self.attributes[ attr.replace('_', '-') ] = value # С заменой underline на дефисы
    
    def __enter__(self): # для использования контекстных менеджеров
        return self # в базовом класе нет поведения, поэтому заглушка
    def __exit__(self, *args, **kwargs): # для использования контекстных менеджеров
        pass # в базовом класе нет поведения, поэтому заглушка

    def __iadd__(self, other): # перегрузка оператора '+='
       
        # Определим поведение только в случае добавления нашей сущности
        if isinstance(other, Tag):  # if type(other) is Tag: - не подойдёт т.к. в HTML будем добавлять TopLevelTag, а он не Tag
            self.children.append(other)
        return self

    def __str__(self):
        # переписал __str__ с учётом нового метода Tag.get_lines()
        return '\n'.join(self.get_lines())

    def get_lines(self, indent = None, set_offset = 0): 
        """
        Метод вернёт текущий тэг со всем его содержимым в виде списка строк, что удобно для будущего добавления отступов.
        indent -- оступы для внутрненних элементов. 
        set_offset -- сдвиг элемента на set_offset отступов. Сделана с заделом на будущее использование класса и вставки тэга 
        внутрь существующего HTML-документа.
        """
        if indent is None: # __str__ использует indent=None, поэтому если необходимо переназначить отступы - сделай это в коде до вызова __str__
            indent = self.indent

        attrs = []
        for attr, value in self.attributes.items():
            attrs.append('%s="%s"' % (attr, value))
        attrs = ' '.join(attrs)

        if self.is_single: # одиночный тег не содержит вложенных тегов и внутреннего текста, поэтому отображается одной строкой
            return [f'{set_offset*indent}<{self.tag}{" " + attrs if attrs else ""}/>'] # Конструкция {" " if attrs else ""} заберёт пробел в случае отсутствия аргументов        
        
                    
        # обработчик двойных тегов
        lines = []
        lines.append(f'<{self.tag}{" " + attrs if attrs else ""}>') # добавим строку открывающего тега с его свойствами
        if self.text:
            lines.append(indent + self.text )
        
        # каждой строке внутреннего тега добавим отступ
        # осторожно, рекурсия!
        for inner in self.children: # для каждого потомка ...
            lines += [indent + line for line in inner.get_lines(indent)] # каждая его строка склеивается с отступом и весь его список строк добавляем в наш текущий
        
        lines.append(f'</{self.tag}>') # добавим строку с закрывающии тегом
        
        if set_offset:
            return [(set_offset*indent) + line for line in lines]
        return lines
        

class TopLevelTag(Tag):
    """
    Класс для добавления тегов верхнего уровня, например, <body>, <head>.
    Создан скорее для визуального отделения обычных тегов от верхних. Является всегда парным.
    """
    def __init__(self, tag, **kwargs):
        super().__init__(tag, **kwargs) # задействуем конструктор наследуемого класса super().__init__

class HTML(Tag):
    """
    Класс реализует обёртку для тегов TopLevelTag(), Tag() -- html. 
    Вернёт файл, если указать путь в out_filepath(str), иначе - выведет на экран.
    Поддерживается контекст. При выходе из контекста автоматически вызовется .flush().
    Для записи содержимого в файл / вывода на экран  -- вызвать метод .flush().
    """
    def __init__(self, out_filepath=None):
        self.output = out_filepath
        super().__init__(tag = 'html')
    
    def __exit__(self, *args, **kwargs):
        self.flush()
    
    def flush(self): # функция принудительного вывода на экран / в файл -- использовать при работе без контекста with
        if not type(self.output) is str:
            print(self)
        else:
            with open(self.output, mode='w', encoding='UTF-8') as fp:                
                fp.write('\n'.join(self.get_lines(indent = self.indent)))
        




# if __name__ == '__main__':
#     doc = HTML('out.txt')
#     with TopLevelTag('body') as body:
#         with Tag('div', klass='container') as my_div:
#             my_div.text = 'Lorem ipsum'
#             with Tag('img', klass=('my_image', "photo"), is_single=True, src = '/img/photo1.png', alt="It's me", un_der = "true") as my_img:
#                 my_div += my_img
#             with Tag('div', klass=('row', 'no-gutters')) as row:
#                 # with Tag('div', klass=('col', 'col-3-sm')) as col:
#                 #     row += col
#                 my_div += row            
#             body += my_div
#         doc += body
    
#     doc.flush()
#     print(doc)




# Из примера:


if __name__ == "__main__":
    with HTML(out_filepath=None) as doc:
        # doc.indent = '--'
        with TopLevelTag("head") as head:
            with Tag("title") as title:
                title.text = "hello"
                head += title
            doc += head

        with TopLevelTag("body") as body:
            with Tag("h1", klass=("main-text",)) as h1:
                h1.text = "Test"
                body += h1
            # body.indent = '%%'
            with Tag("div", klass=("container", "container-fluid"), id="lead") as div:
                with Tag("p") as paragraph:
                    paragraph.text = "another test"
                    div += paragraph

                with Tag("img", is_single=True, src="/icon.png") as img:
                    div += img

                body += div
            # for _ in body.get_lines(set_offset=4):
                # print(_)
            doc += body








    # def __str__(self):
    #     """Старая функция __str__"""
    #     # Переводим словарь аттрибутов с строку, разделяя их пробелами
    #     attrs = []
    #     for attr, value in self.attributes.items():
    #         attrs.append('%s="%s"' % (attr, value))
    #     attrs = ' '.join(attrs)
    #     # различия в выхлопе при самозакрывающихся тегах
    #     if self.is_single:
    #         return '<%s %s/>' % (self.tag, attrs)
    #     else:
    #         children = '' # эта инициализация потребуется `для выхлопа при отстутсвии потомков тега
    #         if self.children:
    #             children = []
    #             for child in self.children:
    #                 children.append(str(child))
    #             # children = '\n'.join(children)
    #             children = '\n\t' + '\n\t'.join(children) + '\n'
    #         return '<{tag} {attrs}>{text}{children}</{tag}>'.format(tag = self.tag, attrs = attrs, text = self.text, children = children)
