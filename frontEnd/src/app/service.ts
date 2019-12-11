
import {HttpClient, HttpResponse} from '@angular/common/http';
import {Injectable} from '@angular/core';

@Injectable({
  providedIn: 'root'
})

export class Service {

  constructor(private http: HttpClient) {

  }

  loadCheckoutData() {
    const url = `http://localhost:5000/painTable`;
    return this.http.get<any>(url);
  }

}
