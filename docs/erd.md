# ERD — microservice-pencari-tuhan

> Setiap service punya database terpisah. Relasi antar service **tidak** melalui foreign key DB,
> melainkan melalui ID reference (aplikasi yang menjaga konsistensinya).

---

## Auth Service DB (`postgres_auth`)

```mermaid
erDiagram
    USERS {
        uuid        id          PK
        string      username    "unique"
        string      email       "unique"
        string      password_hash
        string      role        "admin | librarian | member"
        boolean     is_active
        timestamp   created_at
        timestamp   updated_at
    }

    REFRESH_TOKENS {
        uuid        id          PK
        uuid        user_id     FK
        string      token       "unique"
        timestamp   expires_at
        boolean     revoked
        timestamp   created_at
    }

    USERS ||--o{ REFRESH_TOKENS : "has"
```

---

## Book Service DB (`postgres_book`)

```mermaid
erDiagram
    BOOKS {
        uuid        id              PK
        string      title
        string      author
        string      isbn            "unique"
        string      publisher
        string      category        "for kategori buku mgmt + search filter"
        text        description     "nullable"
        int         year
        int         total_copies
        int         available_copies
        timestamp   created_at
        timestamp   updated_at
    }
```

---

## Member Service DB (`postgres_member`)

```mermaid
erDiagram
    MEMBERS {
        uuid        id          PK
        uuid        user_id     "ref: auth.users.id, unique"
        string      full_name
        string      email       "unique"
        string      phone
        string      address
        enum        status      "active | inactive | blocked"
        timestamp   created_at
        timestamp   updated_at
    }
```

---

## Loan Service DB (`postgres_loan`)

```mermaid
erDiagram
    LOANS {
        uuid        id          PK
        uuid        member_id   "ref: member.members.id"
        uuid        book_id     "ref: book.books.id"
        date        loan_date
        date        due_date
        date        return_date "nullable"
        string      status      "active | returned | overdue"
        timestamp   created_at
        timestamp   updated_at
    }
```

---

## Fine Service DB (`postgres_fine`)

```mermaid
erDiagram
    FINES {
        uuid        id          PK
        uuid        loan_id     "ref: loan.loans.id"
        uuid        member_id   "ref: member.members.id"
        decimal     amount
        boolean     is_paid
        timestamp   paid_at     "nullable"
        timestamp   created_at
        timestamp   updated_at
    }
```

---

## Cross-Service Reference Rules

- `loan.member_id` → Member Service di-query via httpx untuk validasi
- `loan.book_id` → Book Service di-query via httpx untuk cek & update stok
- `fine.loan_id` → Loan Service di-query untuk detail keterlambatan
- Tidak ada foreign key lintas database — konsistensi dijaga di application layer

---

## Changelog (Sprint 3 — Book & Member implementation)

- `BOOKS`: tambah `category` + `description` — proposal BAB IV Modul 1 nyebut atribut ini di deskripsi buku, sebelumnya gak ada di ERD. Dipakai juga buat `GET /books/search`.
- `MEMBERS`: ganti `is_active (boolean)` → `status (enum: active/inactive/blocked)` — proposal nyebut 3 status keanggotaan eksplisit (`PATCH /members/{id}/status`), boolean gak cukup buat representasiin "blocked".
