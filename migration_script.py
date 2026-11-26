#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migration_script.py
-------------------
মাদরাসাতুল বালাগ — ডিজিটাল ম্যানেজমেন্ট সিস্টেম
পুরোনো শরয়ী ফান্ডের গোরাবা ফান্ডে সঙ್ಗ্রহ স্ক্রিপ্ট

এই স্ক্রিপ্টটি বিদ্যমান masjid_data.db ডেটাবেস থেকে পুরোনো আলাদা শরয়ী ফান্ডগুলো
নিরাপদে একত্র করে 'গোরাবা ফান্ড' মধ্যে নিয়ে আসে:

  * যাকাত ফান্ড
  * ফিতরা ফান্ড
  * চামড়া ফান্ড
  * সাদকা ফান্ড

প্রতিটি পুরোনো ফান্ডের ব্যালেন্স গোরাবা ফান্ডে যোগ করা হয়, সংশ্লিষ্ট
লেনদেনের fund_name আপডেট করা হয় এবং পুরোনো ফান্ড রো ডিলিট করা হয়।

চালানোর উপায়:
    python3 migration_script.py
"""

import sqlite3
import sys

DB_PATH = "masjid_data.db"

# পুরোনো আলাদা শরয়ী ফান্ডের তালিকা যেগুলো গোরাবা ফান্ডে একত্রিত হবে
OLD_GORABA_FUNDS = [
    "যাকাত ফান্ড",
    "ফিতরা ফান্ড",
    "চামড়া ফান্ড",
    "সদকা ফান্ড",
]

TARGET_FUND = "গোরাবা ফান্ড"


def migrate(db_path=DB_PATH):
    """পুরোনো শরয়ী ফান্ডগুলো গোরাবা ফান্ডে একত্রিত করা।"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # গোরাবা ফান্ডের উপস্থিতি নিশ্চিত করা (নতুন ডেটাবেসের জন্য)
    cursor.execute(
        "INSERT OR IGNORE INTO funds (name, type, balance) VALUES (?, ?, 0.0)",
        (TARGET_FUND, "গোরাবা ফান্ড"),
    )

    migrated_any = False

    for old_fund in OLD_GORABA_FUNDS:
        cursor.execute(
            "SELECT id, balance FROM funds WHERE name = ?", (old_fund,)
        )
        old_row = cursor.fetchone()
        if old_row is None:
            # এই নামের ফান্ড কিছু নেই—কিছুর প্রয়োজন নেই
            continue

        old_fund_id, old_balance = old_row
        old_balance = old_balance or 0.0

        # ১. পুরোনো ফান্ডের ব্যালেন্স গোরাবা ফান্ডে যোগ করা
        if old_balance:
            cursor.execute(
                "UPDATE funds SET balance = balance + ? WHERE name = ?",
                (old_balance, TARGET_FUND),
            )

        # ২. পুরোনো ফান্ডের সব লেনদেনের fund_name আপডেট করা
        cursor.execute(
            "UPDATE transactions SET fund_name = ? WHERE fund_name = ?",
            (TARGET_FUND, old_fund),
        )

        # ৩. পুরোনো ফান্ড রো ডিলিট করা
        cursor.execute(
            "DELETE FROM funds WHERE name = ?", (old_fund,)
        )

        migrated_any = True
        print(
            f"[মাইগ্রেট করা হলো] '{old_fund}' → '{TARGET_FUND}' "
            f"(ব্যালেন্স: {old_balance:.2f} ৳)"
        )

    conn.commit()
    conn.close()

    if migrated_any:
        print(
            "\n[সফল] পুরোনো শরয়ী ফান্ডগুলো গোরাবা ফান্ডে একত্রিত করা হয়েছে।"
        )
    else:
        print(
            "\n[তথ্য] কোনো পুরোনো শরয়ী ফান্ড পাওয়া গেলনি — "
            "মাইগ্রেশনের প্রয়োজন নেই।"
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(migrate())
    except sqlite3.Error as exc:
        print(
            f"[ভুল] ডেটাবেস মাইগ্রেশনে সমস্যা হয়েছে: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"[ভুল] ডেটাবেস ফাইল পাওয়া যায়নি: {DB_PATH}",
            file=sys.stderr,
        )
        sys.exit(1)
