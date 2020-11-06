import FCMManager as fcm

tokens = ["dYV58gaxRxiJrEgPdG8a5i:APA91bF1kC1_OkoR0yLx4GaFiGbRWthIlo1tJhPVrNYcOlp-J_11VQIe3BhQukK4ctK0y_PmyCJQcDm64sVhGhy"
          "-6WUq11eitr8RbiRMi6677Koloxwzcomq9Mpx4Oq0A3T51GXusGOu"]
#fIQFEqcXTo-pgttuHRjdKt:APA91bEbX7Gfank-D7szc1AbmLwBCazGERyxft5hZ06XtEaAZ2Qvqr_McVNyZGVkexP3A1hzDXie5rJ0deQ2LivpYM2Lp2U0iu7wTWxi6Pp1mKfg_rjdrq8P28Ri6fflARrX3SgCStYo
#"dYV58gaxRxiJrEgPdG8a5i:APA91bF1kC1_OkoR0yLx4GaFiGbRWthIlo1tJhPVrNYcOlp-J_11VQIe3BhQukK4ctK0y_PmyCJQcDm64sVhGhy"
#          "-6WUq11eitr8RbiRMi6677Koloxwzcomq9Mpx4Oq0A3T51GXusGOu"
fcm.sendPush("Hi", "This is my next msg", tokens)
