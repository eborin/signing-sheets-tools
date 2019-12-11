import {Signature} from './signature';

export class Student {
  // tslint:disable-next-line:variable-name
  private _ra: number;
  private _signatures: Array<Signature>;

  get ra(): number {
    return this._ra;
  }

  set ra(value: number) {
    this._ra = value;
  }

  get signatures(): Array<Signature> {
    return this._signatures;
  }

  set signatures(value: Array<Signature>) {
    this._signatures = value;
  }

  static decode(studentsJSON) {
    const students = [];
    for (const studentJSON of studentsJSON.students) {
      const student = new Student();
      student.ra = studentJSON.ra;
      student.signatures = Signature.decode(studentJSON.signatures);
      students.push(student);
    }
    return students;
  }
}
