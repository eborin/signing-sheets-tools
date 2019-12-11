import {Component, OnInit} from '@angular/core';
import { Service } from './service';
import {Student} from './student';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'frontEnd';
  listaPresenca: Array<Student>;

  constructor(private service: Service) { }

  ngOnInit() {


  }

  async loadLista() {
    try {
      const result = await this.service.loadCheckoutData().toPromise();
      this.listaPresenca = Student.decode(result);
    } catch (e) {
      console.log(e);
    }
  }

}


