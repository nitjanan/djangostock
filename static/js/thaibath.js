function ThaiNumberToText(num) {
    num = num.toString();
    num = num.replace(/๐/g, '0')
             .replace(/๑/g, '1')
             .replace(/๒/g, '2')
             .replace(/๓/g, '3')
             .replace(/๔/g, '4')
             .replace(/๕/g, '5')
             .replace(/๖/g, '6')
             .replace(/๗/g, '7')
             .replace(/๘/g, '8')
             .replace(/๙/g, '9');
    return ArabicNumberToText(num);
}

function ArabicNumberToText(Number) {
    Number = CheckNumber(Number);
    let NumberArray = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"];
    let DigitArray = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"];
    let BahtText = "";

    if (isNaN(Number)) {
        return "ข้อมูลนำเข้าไม่ถูกต้อง";
    }

    // แยกจำนวนเต็มกับทศนิยม
    let parts = Number.split(".");
    let integerPart = parts[0];
    let decimalPart = parts[1].substring(0, 2);

    // แปลงจำนวนเต็มเป็นกลุ่มละ 6 หลัก (เพราะไทยใช้ "ล้าน" ซ้ำ)
    let groups = [];
    while (integerPart.length > 0) {
        let cut = integerPart.slice(-6);
        integerPart = integerPart.slice(0, -6);
        groups.unshift(cut);
    }

    groups.forEach((grp, idx) => {
        let text = "";
        for (let i = 0; i < grp.length; i++) {
            let digit = parseInt(grp.charAt(i));
            if (digit !== 0) {
                if ((i === grp.length - 1) && (digit === 1) && grp.length > 1) {
                    text += "เอ็ด";
                } else if ((i === grp.length - 2) && (digit === 2)) {
                    text += "ยี่";
                } else if ((i === grp.length - 2) && (digit === 1)) {
                    text += "";
                } else {
                    text += NumberArray[digit];
                }
                text += DigitArray[grp.length - i - 1];
            }
        }
        if (text !== "") {
            BahtText += text;
            if (idx < groups.length - 1) {
                BahtText += "ล้าน";
            }
        }
    });

    BahtText += "บาท";

    // ส่วนสตางค์
    if (decimalPart === "0" || decimalPart === "00") {
        BahtText += "ถ้วน";
    } else {
        for (let i = 0; i < decimalPart.length; i++) {
            let digit = parseInt(decimalPart.charAt(i));
            if (digit !== 0) {
                if ((i === decimalPart.length - 1) && (digit === 1) && decimalPart.length > 1) {
                    BahtText += "เอ็ด";
                } else if ((i === decimalPart.length - 2) && (digit === 2)) {
                    BahtText += "ยี่";
                } else if ((i === decimalPart.length - 2) && (digit === 1)) {
                    BahtText += "";
                } else {
                    BahtText += NumberArray[digit];
                }
                BahtText += DigitArray[decimalPart.length - i - 1];
            }
        }
        BahtText += "สตางค์";
    }

    return BahtText;
}

function CheckNumber(Number) {
    let decimal = false;
    Number = Number.toString();
    Number = Number.replace(/ |,|บาท|฿/gi, '');
    for (let i = 0; i < Number.length; i++) {
        if (Number[i] === '.') {
            decimal = true;
        }
    }
    if (!decimal) {
        Number = Number + '.00';
    }
    return Number;
}
