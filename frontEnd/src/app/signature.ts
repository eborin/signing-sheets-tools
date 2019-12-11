export class Signature {

  private _date: string;
  private _raImage: string;
  private _signatureImage: string;
  private _present: string;
  private _similar: string;
  private _checkoutValue: string;

  get date(): string {
    return this._date;
  }

  set date(value: string) {
    this._date = value;
  }

  get raImage(): string {
    return this._raImage;
  }

  set raImage(value: string) {
    this._raImage = value;
  }

  get signatureImage(): string {
    return this._signatureImage;
  }

  set signatureImage(value: string) {
    this._signatureImage = value;
  }

  get present(): string {
    return this._present;
  }

  set present(value: string) {
    this._present = value;
  }

  get similar(): string {
    return this._similar;
  }

  set similar(value: string) {
    this._similar = value;
  }

  get checkoutValue(): string {
    return this._checkoutValue;
  }

  set checkoutValue(value: string) {
    this._checkoutValue = value;
  }

  static decode(signaturesJSON) {
    const signatures = [];
    for (const signatureJSON of signaturesJSON) {
      const signature = new Signature();
      signature.date = signatureJSON.date;
      signature.raImage = signatureJSON.raImage;
      signature.signatureImage = signatureJSON.signatureImage;
      signature.present = signatureJSON.present;
      signature.similar = signatureJSON.similar;
      signature.checkoutValue = signatureJSON.checkoutValue;
      signatures.push(signature);
    }
    return signatures;
  }

}
