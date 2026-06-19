class Yuri < Formula
  desc "Yuri Esoteric Programming Language"
  homepage "https://kazooki123.github.io/yurilang-docs"
  url "https://codeberg.org/Kazooki123/yurilang"
  sha256 "31941F6261FF87D855BAA19FEEC40A8BECE10B5FEE6DCE08B1F9E921993A153B"
  license "GPL-3.0-or-later"

  depends_on "python@3.14"

  def install
    system "bash", "install.sh"

    bin.install "yuri.py" => "yuri"
  end

  test do
    system "#{bin}/yuri", "--version"
  end
end
