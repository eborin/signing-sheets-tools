from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from classes.dao import Dao

KEY_DATE = "date"
KEY_RA_IMAGE = "raImagePath"
KEY_SIGNATURE_IMAGE = "signatureImagePath"
KEY_PRESENT = "present"
KEY_SIMILAR = "similar"
KEY_CHECKOUT = "checkout"
KEY_SIGNATURE_ID = "signatureId"

COLUMN_DATE_WIDTH = 100
COLUMN_RA_IMAGE_WIDTH = 140
COLUMN_SIGNATURE_IMAGE_WIDTH = 240
COLUMN_PRESENT_WIDTH = 100
COLUMN_SIMILAR_WIDTH = 100
COLUMN_CHECKOUT_WIDTH = 100

LABEL_UNKNOWN = "N/A"
LABEL_PRESENT = "Presente"
LABEL_ABSENT = "Ausente"
LABEL_SIMILAR = "Similar"
LABEL_NOT_SIMILAR = "Não similar"
LABEL_NOT_VERIFIED = "Não verificada"
LABEL_CHECKOUT_ABSENT = "A"
LABEL_CHECKOUT_PRESENT_SIMILAR = "PS"
LABEL_CHECKOUT_PRESENT_NOT_SIMILAR = "PNS"
LABEL_CHECKOUT_PRESENT_NOT_VERIFIED = "PNV"

CONST_UNKOWN = -1
CONST_PRESENT = 1
CONST_ABSENT = 0
CONST_SIMILAR = 1
CONST_NOT_SIMILAR = 0
CONST_NOT_VERIFIED = -1
CONST_CHECKOUT_ABSENT = 0
CONST_CHECKOUT_PRESENT_NOT_SIMILAR = 1
CONST_CHECKOUT_PRESENT_NOT_VERIFIED = 2
CONST_CHECKOUT_PRESENT_SIMILAR = 3

Builder.load_string('''

<MainFrame>:
    orientation:'vertical'
    BoxLayout:
        orientation:'horizontal'
        size_hint_y:None
        height:40
        Button:
            text:'Cálculo Automático'
            on_release: root.generateCheckout()
        Button:
            text:'Extrair CSV'
            background_color: 0,1,0,1
            on_release: root.generateCSV()
    ScrollView:
        BoxLayout:
            id:box
            orientation:'vertical'
            size_hint_y:None
            height:self.minimum_height

<StudentHeader>:
    canvas.before:
        Color:
            rgba: 0.7,0.18,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    size_hint_y: None
    height: 40
    orientation: 'horizontal'
    Label:
        id: name
        font_size: 20
    Label:
        id: ra
        font_size: 20

<TableHeader>
    canvas.before:
        Color:
            rgba: 0.8,0.2,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    size_hint_y: None
    height: 40
    orientation: 'horizontal'
    Label:
        id: date
        size_hint_x:None
        width: {0}
        text: "Data"
        font_size: 18
    Label:
        id: raImage
        size_hint_x:None
        width:{1}
        text: "Imagem RA"
        font_size: 18
    Label:
        id: signatureImage
        size_hint_x:None
        width:{2}
        text: "Imagem Assinatura"
        font_size: 18
    Label:
        id: present
        size_hint_x:None
        width:{3}
        text: "Presença"
        font_size: 18
    Label:
        id: similar
        size_hint_x:None
        width:{4}    
        text: "Similar"
        font_size: 18
    Label:
        id: checkout
        size_hint_x:None
        width:{5}
        text: "Final"
        font_size: 18

<TableRow>
    canvas.before:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
    size_hint_y: None
    height: 100
    orientation: 'horizontal'
    Label:
        id: date
        size_hint_x:None
        width:{0}
        color: 0,0,0,1
    Image:
        id: raImage
        size_hint_x:None
        width:{1}
    Image:
        id: signatureImage
        size_hint_x:None
        width:{2}
    Button:
        id: present
        size_hint_x:None
        width:{3}
        color: 0,0,0,1
        background_normal: ''
        background_color: 1,1,1,1
        on_release: root.changePresence()
    Button:
        id: similar
        size_hint_x:None
        width:{4}    
        color: 0,0,0,1
        background_normal: ''
        background_color: 1,1,1,1
        on_release: root.changeSimilarity()
    Button:
        id: checkout
        size_hint_x:None
        width:{5}
        color: 0,0,0,1
        background_normal: ''
        background_color: 1,1,1,1
        on_release: root.changeCheckout()
        
'''.format(COLUMN_DATE_WIDTH, COLUMN_RA_IMAGE_WIDTH, COLUMN_SIGNATURE_IMAGE_WIDTH, COLUMN_PRESENT_WIDTH,
           COLUMN_SIMILAR_WIDTH, COLUMN_CHECKOUT_WIDTH))


class StudentHeader(BoxLayout):
    def __init__(self, raName, **kwargs):
        super().__init__(**kwargs)
        self.ids.ra.text = "RA: {}".format(raName[0])
        self.ids.name.text = "Nome: {}".format(raName[1])


class MainFrame(BoxLayout):
    def __init__(self, students, className, **kwargs):
        super().__init__(**kwargs)
        self.students = students
        self.className = className
        self.rows = {}
        for (raName, signatures) in students.items():
            self.ids.box.add_widget(StudentHeader(raName))
            self.ids.box.add_widget(TableHeader())
            for signature in signatures:
                tableRow = TableRow(signature)
                self.rows[signature[KEY_SIGNATURE_ID]] = tableRow
                self.ids.box.add_widget(tableRow)

    def generateCheckout(self):
        checkoutDic = {}
        for signatureId, tableRow in self.rows.items():
            presence = tableRow.ids.present.text
            similarity = tableRow.ids.similar.text
            if presence == LABEL_PRESENT:
                if similarity == LABEL_SIMILAR:
                    tableRow.ids.checkout.text = LABEL_CHECKOUT_PRESENT_SIMILAR
                    checkoutDic[signatureId] = CONST_CHECKOUT_PRESENT_SIMILAR
                elif similarity == LABEL_NOT_VERIFIED:
                    tableRow.ids.checkout.text = LABEL_CHECKOUT_PRESENT_NOT_VERIFIED
                    checkoutDic[signatureId] = CONST_CHECKOUT_PRESENT_NOT_VERIFIED
                elif similarity == LABEL_NOT_SIMILAR:
                    tableRow.ids.checkout.text = LABEL_CHECKOUT_PRESENT_NOT_SIMILAR
                    checkoutDic[signatureId] = CONST_CHECKOUT_PRESENT_NOT_SIMILAR
            else:
                tableRow.ids.checkout.text = LABEL_CHECKOUT_ABSENT
                checkoutDic[signatureId] = CONST_CHECKOUT_ABSENT

        Dao().generateCheckout(checkoutDic)

    def generateCSV(self):
        Dao().getCheckoutDictionary(self.className)


class TableHeader(BoxLayout):
    pass


class TableRow(BoxLayout):
    def __init__(self, signature, **kwargs):
        super().__init__(**kwargs)
        self.ids.date.text = signature[KEY_DATE]
        self.ids.raImage.source = signature[KEY_RA_IMAGE]
        self.ids.signatureImage.source = signature[KEY_SIGNATURE_IMAGE]
        self.ids.present.text = self.getPresenceString(signature[KEY_PRESENT])
        self.ids.similar.text = self.getSimilarityString(signature[KEY_SIMILAR])
        self.ids.checkout.text = self.getCheckoutString(signature[KEY_CHECKOUT])
        self.signatureId = signature[KEY_SIGNATURE_ID]

    def getPresenceString(self, presence):
        if presence == CONST_ABSENT:
            return LABEL_ABSENT
        elif presence == CONST_PRESENT:
            return LABEL_PRESENT
        else:
            return LABEL_UNKNOWN

    def getSimilarityString(self, similar):
        if similar == CONST_SIMILAR:
            return LABEL_SIMILAR
        elif similar == CONST_NOT_SIMILAR:
            return LABEL_NOT_SIMILAR
        else:
            return LABEL_NOT_VERIFIED

    def getCheckoutString(self, checkout):
        if checkout == CONST_CHECKOUT_ABSENT:
            return LABEL_CHECKOUT_ABSENT
        elif checkout == CONST_CHECKOUT_PRESENT_NOT_SIMILAR:
            return LABEL_CHECKOUT_PRESENT_NOT_SIMILAR
        elif checkout == CONST_NOT_VERIFIED:
            return LABEL_CHECKOUT_PRESENT_NOT_VERIFIED
        elif checkout == CONST_CHECKOUT_PRESENT_SIMILAR:
            return LABEL_CHECKOUT_PRESENT_SIMILAR
        else:
            return LABEL_UNKNOWN

    def changePresence(self):
        newPresence = Dao().switchPresence(self.signatureId)
        self.ids.present.text = self.getPresenceString(newPresence)

    def changeSimilarity(self):
        newSimilarity = Dao().switchSimilarity(self.signatureId)
        self.ids.similar.text = self.getSimilarityString(newSimilarity)

    def changeCheckout(self):
        newCheckout = Dao().switchCheckout(self.signatureId)
        self.ids.checkout.text = self.getCheckoutString(newCheckout)


class InterfaceApp(App):
    def __init__(self, className, **kwargs):
        students = Dao().getCheckoutDictionary(className)
        super().__init__(**kwargs)
        self.students = students
        self.className = className

    def build(self):
        return MainFrame(self.students, self.className)
